import uuid
from typing import Union

from django.urls import reverse
from faker import Faker
from rest_framework import status

import exceptions
from confirm.choices import TypeConfirm, ObjConfirm
from confirm.models import ConfirmEmail, ConfirmPhone
from tests.confirm.factories import ConfirmEmailFactory, ConfirmPhoneFactory
from tests.utils import BaseE2ETest, create_base_user

faker = Faker()


class RegistrationE2ETest(BaseE2ETest):
    def setUp(self):
        self.url = reverse('user:registration')

    @staticmethod
    def generate_request_data(secret_code: uuid.UUID, obj_confirm: ObjConfirm):
        password = 'Adw32Ffaw234adw'
        return {
            'secret_code': secret_code,
            'password': password,
            'confirm_password': password,
            'object_confirm': obj_confirm
        }

    def check_fail_passwd_not_equal(self, confirm_obj: Union[ConfirmEmail, ConfirmPhone], obj_confirm: ObjConfirm):
        request_data = self.generate_request_data(confirm_obj.secret_code, obj_confirm)
        request_data['confirm_password'] = 'ADw32aFawfaw322'
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.PasswordNotEqual)

    def test_success(self):
        # Регистрация по email
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        request_data = self.generate_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

        # Регистрация по телефону
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        request_data = self.generate_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

    def test_fail(self):
        # Пароли не совпадают
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        self.check_fail_passwd_not_equal(confirm_obj, ObjConfirm.EMAIL)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        self.check_fail_passwd_not_equal(confirm_obj, ObjConfirm.PHONE)

        # Код подтверждения не найден
        # EMAIL
        request_data = self.generate_request_data(uuid.uuid4(), ObjConfirm.EMAIL)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotFound)

        # PHONE
        request_data = self.generate_request_data(uuid.uuid4(), ObjConfirm.PHONE)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotFound)

        # Код подтверждения не для регистрации
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        request_data = self.generate_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotFound)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        request_data = self.generate_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotFound)

        # Код подтверждения не подтвержден
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=False)
        request_data = self.generate_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotConfirmed)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=False)
        request_data = self.generate_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.ConfirmObjNotConfirmed)

        # Пользователь с таким Email уже есть в системе
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        create_base_user(email=confirm_obj.email)
        request_data = self.generate_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserAlreadyExist)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        create_base_user(phone=confirm_obj.phone)
        request_data = self.generate_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserAlreadyExist)
