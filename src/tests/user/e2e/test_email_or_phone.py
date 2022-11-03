import uuid

from django.urls import reverse
from faker import Faker
from rest_framework import status

import exceptions
from confirm.choices import TypeConfirm, ObjConfirm
from tests.confirm.factories import ConfirmEmailFactory, ConfirmPhoneFactory
from tests.utils import BaseE2ETest, create_base_user, rand_mobile_phone

faker = Faker()


class ChangeEmailOrPhone2ETest(BaseE2ETest):
    def setUp(self):
        self.url = reverse('user:change_email_or_phone')
        user = create_base_user(email=faker.email(), phone=rand_mobile_phone()['phone'])
        self.set_bearer_credentials(user)

    @staticmethod
    def get_request_data(secret_code: uuid.UUID, object_confirm: ObjConfirm):
        return {
            'secret_code': secret_code,
            'object_confirm': object_confirm
        }

    def check_fail(self, request_data, exception):
        response_data = self.client.patch(self.url, data=request_data)
        self.conflict_response(response_data, exception)

    def test_success(self):
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        response_data = self.client.patch(self.url, data=request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        response_data = self.client.patch(self.url, data=request_data)
        self.assertEqual(response_data.status_code, status.HTTP_204_NO_CONTENT)

    def test_fail(self):
        # Передан не существующий secret_code
        # EMAIL
        request_data = self.get_request_data(uuid.uuid4(), ObjConfirm.EMAIL)
        self.check_fail(request_data, exceptions.ConfirmObjNotFound)

        # PHONE
        request_data = self.get_request_data(uuid.uuid4(), ObjConfirm.PHONE)
        self.check_fail(request_data, exceptions.ConfirmObjNotFound)

        # Объект подтверждения не подтвержден
        confirm_data = {'confirmed': False, 'type_confirm': TypeConfirm.CHANGE}
        # EMAIL
        confirm_obj = ConfirmEmailFactory(**confirm_data)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        self.check_fail(request_data, exceptions.ConfirmObjNotConfirmed)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(**confirm_data)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        self.check_fail(request_data, exceptions.ConfirmObjNotConfirmed)

        # Объект подтвержден, но он не для изменения email
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        self.check_fail(request_data, exceptions.ConfirmObjNotFound)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=False)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        self.check_fail(request_data, exceptions.ConfirmObjNotFound)

        # В системе есть пользователь с таким email
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        create_base_user(email=confirm_obj.email)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.EMAIL)
        self.check_fail(request_data, exceptions.UserAlreadyExist)

        # В системе есть пользователь с таким телефоном
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        create_base_user(phone=confirm_obj.phone)
        request_data = self.get_request_data(confirm_obj.secret_code, ObjConfirm.PHONE)
        self.check_fail(request_data, exceptions.UserAlreadyExist)
