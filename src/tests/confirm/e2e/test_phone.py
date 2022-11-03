import uuid
from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework import status

import exceptions
from confirm.choices import TypeConfirm, ObjConfirm, PhoneRegion
from tests.confirm.factories import ConfirmPhoneFactory
from tests.utils import BaseE2ETest, create_base_user, rand_mobile_phone

faker = Faker()


class CreateConfirmPhoneE2ETest(BaseE2ETest):
    def setUp(self):
        self.url = reverse('confirm:create_confirm_phone')

    @staticmethod
    def get_request_data(type_confirm: TypeConfirm, phone_number: str):
        return {
            'type_confirm': type_confirm,
            'phone': phone_number,
            'region': PhoneRegion.RUSSIAN
        }

    def check_success_request(self, request_data):
        response_data = self.client.post(self.url, request_data)

        self.assertEqual(response_data.status_code, status.HTTP_201_CREATED)
        response_data = response_data.json()
        self.assertIn('secret_code', response_data)
        self.assertIn('sec_resend', response_data)
        self.assertIn('count_resend', response_data)

    @patch('confirm.views.task_send_confirm_code_phone')
    def test_success(self, task_send_confirm_code_phone):
        """
        Успешное создание кода подтверждения для телефона
        """

        # Регистрация
        request_data = self.get_request_data(TypeConfirm.REGISTRATION, rand_mobile_phone()['number'])
        self.check_success_request(request_data)

        # Изменение номера телефона
        request_data = self.get_request_data(TypeConfirm.CHANGE, rand_mobile_phone()['number'])
        self.check_success_request(request_data)

        # Сброс пароля по номеру телефона
        phone = rand_mobile_phone()
        create_base_user(phone=phone['phone'])
        request_data = self.get_request_data(TypeConfirm.RESET_PASS, phone['number'])
        self.check_success_request(request_data)

    @patch('confirm.views.task_send_confirm_code_phone')
    def test_fail(self, task_send_confirm_code_phone):
        """
        Невозможно создать код подтверждения
        """

        # Некорректный номер телефона
        request_data = self.get_request_data(TypeConfirm.REGISTRATION, '92311111')
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.IncorrectPhone)

        # Невозможно создать код подтверждения для регистрации, пользователь уже есть с таким номером
        phone = rand_mobile_phone()
        create_base_user(phone=phone['phone'])
        request_data = self.get_request_data(TypeConfirm.REGISTRATION, phone['number'])
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserAlreadyExist)

        # Невозможно создать код подтверждения для смены номера телефона, пользователь уже есть с таким номером
        request_data['type_confirm'] = TypeConfirm.CHANGE
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserAlreadyExist)

        # Невозможно создать код подтверждения для сброса пароля, когда пользователя нет в системе
        request_data = self.get_request_data(TypeConfirm.RESET_PASS, rand_mobile_phone()['number'])
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserNotFound)

        # Невозможно создать код подтверждения, так как он был создан ранние, нужно подождать
        # n-е кол-во секунд для следующей отправки
        phone = rand_mobile_phone()
        confirm_obj = ConfirmPhoneFactory(phone=phone['phone'])
        request_data = self.get_request_data(TypeConfirm.REGISTRATION, phone['number'])
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_409_CONFLICT)
        response_data = response_data.json()
        exc = exceptions.ConfirmPhoneWaitBeforeSending(confirm_obj.sec_resend)
        self.assertEqual(response_data['detail'], exc.message)
        self.assertEqual(response_data['code'], exc.code)
        self.assertEqual(response_data['payload_data']['wait_seconds'], exc.payload_data['wait_seconds'])

        # Невозможно отправить код подтверждения, так как количество попыток истекло
        phone = rand_mobile_phone()
        ConfirmPhoneFactory(phone=phone['phone'], count_send=settings.PHONE_CONFIRM_CODE_COUNT_SEND)
        request_data = self.get_request_data(TypeConfirm.REGISTRATION, phone['number'])
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_409_CONFLICT)
        response_data = response_data.json()
        exc = exceptions.ConfirmPhoneExcMaxCountSend(settings.PHONE_CONFIRM_RESET_COUNT_SEND_SECONDS)
        self.assertEqual(response_data['detail'], exc.message)
        self.assertEqual(response_data['code'], exc.code)
        self.assertEqual(response_data['payload_data']['wait_seconds'], exc.payload_data['wait_seconds'])


class ConfirmPhoneE2ETest(BaseE2ETest):
    """
    Подтверждение номера телефона
    """

    def setUp(self):
        self.url = reverse('confirm:confirm')

    @staticmethod
    def get_request_data(secret_code: uuid.UUID, confirm_code: str):
        return {
            'secret_code': secret_code,
            'confirm_code': confirm_code,
            'object_confirm': ObjConfirm.PHONE
        }

    def test_success_confirm_phone(self):
        """
        Успешное подтверждение phone
        """

        confirm_obj = ConfirmPhoneFactory()
        request_data = self.get_request_data(confirm_obj.secret_code, confirm_obj.confirm_code)
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

    def test_fail_confirm_phone(self):
        """
        Невозможно подтвердить phone
        """

        # Переданы неверные secret_code или confirm_code
        request_data = self.get_request_data(uuid.uuid4(), '123321')
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotFound)

        # Объект уже подтвержден
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        request_data = self.get_request_data(confirm_obj.secret_code, confirm_obj.confirm_code)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotFound)

        # Время для подтверждения истекло
        ttl_hours = settings.PHONE_VER_TTL_HOURS
        confirm_obj = ConfirmPhoneFactory(
            created_at=timezone.now() - timezone.timedelta(hours=ttl_hours + 1)
        )
        request_data = self.get_request_data(confirm_obj.secret_code, confirm_obj.confirm_code)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmCodeExpired)
