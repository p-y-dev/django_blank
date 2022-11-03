import uuid

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from faker import Faker

import exceptions
from confirm import handlers
from confirm.models import ConfirmPhone
from confirm.choices import TypeConfirm, ObjConfirm, PhoneRegion
from tests.confirm.factories import ConfirmPhoneFactory
from tests.utils import create_base_user, rand_mobile_phone

faker = Faker()


class CreateConfirmPhoneHandlersTest(TestCase):
    def check_success(self, number_phone: str, type_confirm: TypeConfirm):
        """
        Проверка создания/обновления кода подтверждения телефона с использованием всех попыток
        """

        for number_send in range(1, settings.PHONE_CONFIRM_CODE_COUNT_SEND + 1):
            confirm_phone = handlers.create_confirm_phone(
                number_phone, PhoneRegion.RUSSIAN, type_confirm
            )

            self.assertIsInstance(confirm_phone, ConfirmPhone)

            confirm_phone_db = ConfirmPhone.objects.filter(
                id=confirm_phone.id,
                phone=confirm_phone.phone,
                type_confirm=confirm_phone.type_confirm,
                secret_code=confirm_phone.secret_code,
                confirm_code=confirm_phone.confirm_code,
                confirmed=False,
                count_send=number_send
            )
            self.assertTrue(confirm_phone_db.exists())
            confirm_phone_db = confirm_phone_db.get()

            if confirm_phone_db.count_resend == 0:
                self.assertEqual(confirm_phone_db.sec_resend, 0)
            else:
                wait_second_resend = confirm_phone_db.count_send * settings.PHONE_CONFIRM_STEP_WAITING_SECONDS
                self.assertEqual(confirm_phone_db.sec_resend, wait_second_resend)

            # Переназначаем время создания имитирую ожидание для следующей отправки
            wait_second = timezone.timedelta(seconds=confirm_phone_db.sec_resend)
            wait_next_sending = confirm_phone_db.created_at - wait_second
            ConfirmPhone.objects.filter(id=confirm_phone_db.id).update(created_at=wait_next_sending)

    def check_fail(self, phone, type_confirm, exception):
        with self.assertRaises(exception):
            handlers.create_confirm_phone(phone, PhoneRegion.RUSSIAN, type_confirm)

    def test_success(self):
        """
        Успешное создание объекта подтверждения phone
        """

        # Регистрация
        self.check_success(rand_mobile_phone()['number'], TypeConfirm.REGISTRATION)

        # Смена номера
        self.check_success(rand_mobile_phone()['number'], TypeConfirm.CHANGE)

        # Сброс пароля
        phone = rand_mobile_phone()
        create_base_user(phone=phone['phone'])
        self.check_success(phone['number'], TypeConfirm.RESET_PASS)

        # У объекта подтверждения использованы все попытки для отправки кода, но прошло достаточно времени,
        # что бы восстановить счетчик попыток
        phone = rand_mobile_phone()
        type_confirm = TypeConfirm.REGISTRATION
        confirm_obj = ConfirmPhoneFactory(
            phone=phone['phone'], type_confirm=type_confirm, count_send=settings.PHONE_CONFIRM_CODE_COUNT_SEND
        )
        wait_second = timezone.timedelta(seconds=settings.PHONE_CONFIRM_RESET_COUNT_SEND_SECONDS)
        wait_next_sending = confirm_obj.created_at - wait_second
        confirm_obj.created_at = wait_next_sending
        ConfirmPhone.objects.filter(id=confirm_obj.id).update(created_at=wait_next_sending)
        self.check_success(phone['number'], type_confirm)

    def test_fail(self):
        """
        Невозможно создать объект подтверждения phone
        """

        # Некорректный номер телефона
        self.check_fail('3453455', TypeConfirm.REGISTRATION, exceptions.IncorrectPhone)

        # Регистрация
        phone = rand_mobile_phone()
        create_base_user(phone=phone['phone'])

        self.check_fail(phone['number'], TypeConfirm.REGISTRATION, exceptions.UserAlreadyExist)
        self.assertFalse(ConfirmPhone.objects.filter(phone=phone['phone']).exists())

        # Изменение
        self.check_fail(phone['number'], TypeConfirm.CHANGE, exceptions.UserAlreadyExist)
        self.assertFalse(ConfirmPhone.objects.filter(phone=phone['phone']).exists())

        # Сброс пароля
        phone = rand_mobile_phone()
        self.check_fail(phone['number'], TypeConfirm.RESET_PASS, exceptions.UserNotFound)
        self.assertFalse(ConfirmPhone.objects.filter(phone=phone['phone']).exists())

        # В системе уже создан объект подтверждения, для повторного создания он должен подождать n секунд
        phone = rand_mobile_phone()
        type_confirm = TypeConfirm.REGISTRATION
        confirm_obj = ConfirmPhoneFactory(phone=phone['phone'], type_confirm=type_confirm)
        self.check_fail(phone['number'], type_confirm, exceptions.ConfirmPhoneWaitBeforeSending)
        # Объект подтверждения не должен обновиться
        confirm_obj = ConfirmPhone.objects.filter(
            id=confirm_obj.id, secret_code=confirm_obj.secret_code, confirm_code=confirm_obj.confirm_code
        ).exists()
        self.assertTrue(confirm_obj)

        # В системе уже создан объект подтверждения и потрачены все попытки для создания.
        # Для повторного создания он должен подождать n секунд
        phone = rand_mobile_phone()
        type_confirm = TypeConfirm.REGISTRATION
        confirm_obj = ConfirmPhoneFactory(
            phone=phone['phone'], type_confirm=type_confirm, count_send=settings.PHONE_CONFIRM_CODE_COUNT_SEND
        )
        self.check_fail(phone['number'], type_confirm, exceptions.ConfirmPhoneExcMaxCountSend)
        # Объект подтверждения не должен обновиться
        confirm_obj = ConfirmPhone.objects.filter(
            id=confirm_obj.id,
            secret_code=confirm_obj.secret_code,
            confirm_code=confirm_obj.confirm_code,
            count_send=settings.PHONE_CONFIRM_CODE_COUNT_SEND
        ).exists()
        self.assertTrue(confirm_obj)


class ConfirmPhoneHandlersTest(TestCase):
    """
    Тесты на подтверждение phone
    """

    def check_fail(self, secret_code, confirm_code, exception):
        with self.assertRaises(exception):
            handlers.confirm_obj(secret_code, confirm_code, ObjConfirm.PHONE)

        self.assertFalse(ConfirmPhone.objects.filter(
            secret_code=secret_code, confirm_code=confirm_code, confirmed=True
        ).exists())

    def test_success_confirm_phone(self):
        """
        Успешное подтверждение phone
        """

        confirm_obj = ConfirmPhoneFactory()
        self.assertFalse(confirm_obj.confirmed)

        handlers.confirm_obj(confirm_obj.secret_code, confirm_obj.confirm_code, ObjConfirm.PHONE)

        confirm_obj = ConfirmPhone.objects.get(id=confirm_obj.id)
        self.assertTrue(confirm_obj.confirmed)

    def test_fail_confirm_phone(self):
        """
        Невозможно подтвердить phone
        """

        # Объект не найден
        self.check_fail(uuid.uuid4(), 'd223ds', exceptions.ConfirmObjNotFound)

        # Объект уже подтвержден
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        with self.assertRaises(exceptions.ConfirmObjNotFound):
            handlers.confirm_obj(confirm_obj.secret_code, confirm_obj.confirm_code, ObjConfirm.PHONE)

        # Время для подтверждения истекло
        ttl_hours = settings.PHONE_VER_TTL_HOURS
        confirm_obj = ConfirmPhoneFactory(created_at=timezone.now() - timezone.timedelta(hours=ttl_hours + 1))
        self.check_fail(confirm_obj.secret_code, confirm_obj.confirm_code, exceptions.ConfirmCodeExpired)
