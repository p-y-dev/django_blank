import uuid

from django.urls import reverse
from faker import Faker
from rest_framework import status

import exceptions
from confirm.choices import TypeConfirm, ObjConfirm
from tests.confirm.factories import ConfirmEmailFactory, ConfirmPhoneFactory
from tests.utils import BaseE2ETest, create_base_user

faker = Faker()


class ChangePasswordE2ETest(BaseE2ETest):
    def setUp(self):
        self.url = reverse('user:change_password')

    @staticmethod
    def get_request_data():
        new_password = 'Dwda323adAWddafwf'
        return {
            'password': new_password,
            'confirm_password': new_password
        }

    def test_success(self):
        user = create_base_user(email=faker.email())
        request_data = self.get_request_data()
        self.set_bearer_credentials(user)
        response_data = self.client.patch(self.url, data=request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

    def test_fail(self):
        # Запрос неавторизованного пользователя
        request_data = self.get_request_data()
        response_data = self.client.patch(self.url, data=request_data)
        self.unauthorized_response(response_data)

        # Пароли не совпадают
        user = create_base_user(email=faker)
        request_data = self.get_request_data()
        request_data['confirm_password'] = 'ADw332feAdww'
        self.set_bearer_credentials(user)
        response_data = self.client.patch(self.url, data=request_data)
        self.conflict_response(response_data, exceptions.PasswordNotEqual)


class ChangePasswordConfirmE2ETest(BaseE2ETest):
    def setUp(self):
        self.url = reverse('user:change_password_by_confirm')

    @staticmethod
    def get_request_data(secret_code: uuid.UUID, obf_confirm: ObjConfirm):
        new_password = 'ADw323AfwwqqqADW22'
        return {
            'secret_code': secret_code,
            'password': new_password,
            'confirm_password': new_password,
            'object_confirm': obf_confirm
        }

    def check_fail(self, request_data, exception):
        response_data = self.client.patch(self.url, data=request_data)
        self.conflict_response(response_data, exception)

    def test_success(self):
        # Email
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        create_base_user(email=confirm_obj.email)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        response_data = self.client.patch(self.url, data=request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

        # Phone
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        create_base_user(phone=confirm_obj.phone)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        response_data = self.client.patch(self.url, data=request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

    def test_fail(self):
        # Переданные пароли не совпадают
        # EMAIL
        request_data = self.get_request_data(uuid.uuid4(), ObjConfirm.EMAIL)
        request_data['confirm_password'] = 'dawd3ADwd323'
        self.check_fail(request_data, exceptions.PasswordNotEqual)

        # PHONE
        request_data['object_confirm'] = ObjConfirm.PHONE
        self.check_fail(request_data, exceptions.PasswordNotEqual)

        # Код подтверждения не найден
        # EMAIL
        request_data = self.get_request_data(uuid.uuid4(), ObjConfirm.EMAIL)
        self.check_fail(request_data, exceptions.ConfirmObjNotFound)

        # PHONE
        request_data['object_confirm'] = ObjConfirm.PHONE
        self.check_fail(request_data, exceptions.ConfirmObjNotFound)

        # Код подтверждения подтвержден, но не на смену пароля
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        self.check_fail(request_data, exceptions.ConfirmObjNotFound)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        self.check_fail(request_data, exceptions.ConfirmObjNotFound)

        # Код подтверждения не подтвержден
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=False, type_confirm=TypeConfirm.RESET_PASS)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        self.check_fail(request_data, exceptions.ConfirmObjNotConfirmed)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=False, type_confirm=TypeConfirm.RESET_PASS)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        self.check_fail(request_data, exceptions.ConfirmObjNotConfirmed)

        # Отсутствует пользователь с email для сброса пароля
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        self.check_fail(request_data, exceptions.UserNotFound)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        self.check_fail(request_data, exceptions.UserNotFound)

