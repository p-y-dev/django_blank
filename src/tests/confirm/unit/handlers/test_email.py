import uuid

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from faker import Faker

import exceptions
from confirm import handlers
from confirm.models import ConfirmEmail
from confirm.choices import TypeConfirm, ObjConfirm
from tests.confirm.factories import ConfirmEmailFactory
from tests.utils import create_base_user

faker = Faker()


class CreateConfirmEmailHandlersTest(TestCase):
    def check_success(self, email, type_confirm):
        confirmation_email = handlers.create_confirm_email(
            email=email,
            type_confirm=type_confirm
        )

        self.assertTrue(confirmation_email.email.islower())

        confirm_email_id = confirmation_email.id

        # Проверка, что объект создался в системе
        self.assertIsInstance(confirmation_email, ConfirmEmail)
        confirmation_email_db = ConfirmEmail.objects.filter(
            id=confirm_email_id,
            email=confirmation_email.email,
            type_confirm=confirmation_email.type_confirm,
            secret_code=confirmation_email.secret_code,
            confirm_code=confirmation_email.confirm_code,
            confirmed=False
        )
        self.assertTrue(confirmation_email_db.exists())

        # При повторном вызове объект подтверждения обновляет данные
        handlers.create_confirm_email(email=email, type_confirm=type_confirm)
        confirmation_email_db = ConfirmEmail.objects.filter(id=confirm_email_id, confirmed=False).get()
        self.assertEqual(confirmation_email.id, confirmation_email_db.id)
        self.assertEqual(confirmation_email.email, confirmation_email_db.email)
        self.assertNotEqual(confirmation_email.secret_code, confirmation_email_db.secret_code)
        self.assertNotEqual(confirmation_email.confirm_code, confirmation_email_db.confirm_code)
        self.assertNotEqual(confirmation_email.created_at, confirmation_email_db.created_at)

    def check_fail(self, email, type_confirm, exception):
        with self.assertRaises(exception):
            handlers.create_confirm_email(email, type_confirm)

    def test_success_create_confirm_email(self):
        """
        Успешное создание объекта подтверждения email
        """

        # Регистрация
        email = faker.email()
        self.check_success(email, TypeConfirm.REGISTRATION)

        # Изменение
        email = faker.email()
        upper_email = email.upper()
        self.check_success(upper_email, TypeConfirm.CHANGE)

        # Сброс пароля
        email = faker.email()
        create_base_user(email=email)
        self.check_success(email, TypeConfirm.RESET_PASS)

    def test_fail_create_confirm_email(self):
        """
        Невозможно создать объект подтверждения email
        """

        # Регистрация
        email = faker.email()
        create_base_user(email=email)
        self.check_fail(email, TypeConfirm.REGISTRATION, exceptions.UserAlreadyExist)

        # Изменение
        self.check_fail(email, TypeConfirm.CHANGE, exceptions.UserAlreadyExist)

        # Сброс пароля
        self.check_fail(faker.email(), TypeConfirm.RESET_PASS, exceptions.UserNotFound)


class ConfirmEmailHandlersTest(TestCase):
    """
    Тесты на подтверждение email
    """

    def check_fail(self, secret_code, confirm_code, exception):
        with self.assertRaises(exception):
            handlers.confirm_obj(secret_code, confirm_code, ObjConfirm.EMAIL)

        self.assertFalse(ConfirmEmail.objects.filter(
            secret_code=secret_code, confirm_code=confirm_code, confirmed=True
        ).exists())

    def test_success_confirm_email(self):
        """
        Успешное подтверждение email
        """

        confirm_obj = ConfirmEmailFactory()
        self.assertFalse(confirm_obj.confirmed)
        handlers.confirm_obj(confirm_obj.secret_code, confirm_obj.confirm_code, ObjConfirm.EMAIL)
        confirm_obj = ConfirmEmail.objects.get(id=confirm_obj.id)
        self.assertTrue(confirm_obj.confirmed)

    def test_fail_confirm_email(self):
        """
        Невозможно подтвердить email
        """

        # Объект не найден
        secret_code = uuid.uuid4()
        confirm_code = 'da23ds'
        self.check_fail(secret_code, confirm_code, exceptions.ConfirmObjNotFound)

        # Объект уже подтвержден
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        with self.assertRaises(exceptions.ConfirmObjNotFound):
            handlers.confirm_obj(confirm_obj.secret_code, confirm_obj.confirm_code, ObjConfirm.EMAIL)

        # Время для подтверждения истекло
        ttl_hours = settings.EMAIL_VER_TTL_HOURS
        confirm_obj = ConfirmEmailFactory(created_at=timezone.now() - timezone.timedelta(hours=ttl_hours + 1))
        self.check_fail(confirm_obj.secret_code, confirm_obj.confirm_code, exceptions.ConfirmCodeExpired)
