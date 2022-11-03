import uuid
from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework import status

import exceptions
from confirm.choices import TypeConfirm, ObjConfirm
from tests.confirm.factories import ConfirmEmailFactory
from tests.utils import BaseE2ETest, create_base_user

faker = Faker()


class CreateConfirmEmailE2ETest(BaseE2ETest):
    """
    Создание объекта подтверждения email
    """

    def setUp(self):
        self.url = reverse('confirm:create_confirm_email')

    @staticmethod
    def get_request_data(type_confirm: TypeConfirm, email=None):
        return {
            'type_confirm': type_confirm,
            'email': faker.email() if email is None else email
        }

    def success_request(self, request_data):
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_201_CREATED)
        response_data = response_data.json()

        self.assertIn('secret_code', response_data)

    @patch('confirm.views.task_send_confirm_code_email')
    def test_success(self, task_send_confirm_code_email):
        """
        Успешное создание кода подтверждения для email
        """

        # Для регистрации
        request_data = self.get_request_data(TypeConfirm.REGISTRATION)
        self.success_request(request_data)

        # Для изменения email
        request_data = self.get_request_data(TypeConfirm.CHANGE)
        self.success_request(request_data)

        # Для сброса пароля
        email = faker.email()
        create_base_user(email=email)
        request_data = self.get_request_data(TypeConfirm.RESET_PASS, email)
        self.success_request(request_data)

    @patch('confirm.views.task_send_confirm_code_email')
    def test_fail(self, task_send_confirm_code_email):
        """
        Невозможно создать код подтверждения
        """

        # Создание подтверждения для регистрации, когда пользователь с таким email уже есть
        email = faker.email()
        create_base_user(email=email)
        request_data = self.get_request_data(TypeConfirm.REGISTRATION, email)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserAlreadyExist)

        # Создание подтверждения для изменения, когда пользователь с таким email уже есть
        request_data['type_confirm'] = TypeConfirm.CHANGE
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserAlreadyExist)

        # Создание подтверждения для сброса пароля, когда пользователя нет в системе
        request_data = self.get_request_data(TypeConfirm.RESET_PASS)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserNotFound)


class ConfirmEmailE2ETest(BaseE2ETest):
    """
    Подтверждение email
    """

    def setUp(self):
        self.url = reverse('confirm:confirm')

    @staticmethod
    def get_request_data(secret_code: uuid.UUID, confirm_code: str):
        return {
            'secret_code': secret_code,
            'confirm_code': confirm_code,
            'object_confirm': ObjConfirm.EMAIL
        }

    def test_success_confirm_email(self):
        """
        Успешное подтверждение email
        """

        confirm_obj = ConfirmEmailFactory()
        request_data = self.get_request_data(confirm_obj.secret_code, confirm_obj.confirm_code)
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

    def test_fail_confirm_email(self):
        """
        Невозможно подтвердить email
        """

        # Переданы неверные secret_code или confirm_code
        request_data = self.get_request_data(uuid.uuid4(), '123456')
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotFound)

        # Объект уже подтвержден
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        request_data = self.get_request_data(confirm_obj.secret_code, confirm_obj.confirm_code)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotFound)

        # Время для подтверждения истекло
        ttl_hours = settings.EMAIL_VER_TTL_HOURS
        confirm_obj = ConfirmEmailFactory(created_at=timezone.now() - timezone.timedelta(hours=ttl_hours + 1))
        request_data = self.get_request_data(confirm_obj.secret_code, confirm_obj.confirm_code)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmCodeExpired)
