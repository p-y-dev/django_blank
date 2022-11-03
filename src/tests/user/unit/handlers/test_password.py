import uuid

from django.contrib.auth.hashers import check_password
from django.test import TestCase
from faker import Faker

import exceptions
import user.handlers.password as handlers
from confirm.choices import TypeConfirm, ObjConfirm
from confirm.models import ConfirmEmail, ConfirmPhone
from tests.confirm.factories import ConfirmEmailFactory, ConfirmPhoneFactory
from tests.utils import create_base_user
from user.models import User
from typing import Union

faker = Faker()


class ChangePasswordHandlerTest(TestCase):
    def test_success(self):
        old_password = faker.password()
        user = create_base_user(email=faker.email, password=old_password)

        new_password = faker.password()
        handlers.change_password(user, new_password, new_password)

        user = User.objects.get(email=user.email)
        self.assertFalse(check_password(old_password, user.password))
        self.assertTrue(check_password(new_password, user.password))

    def test_fail(self):
        # Пароли не совпадают
        old_password = faker.password()
        user = create_base_user(email=faker.email, password=old_password)
        with self.assertRaises(exceptions.PasswordNotEqual):
            handlers.change_password(user, faker.password(), faker.password())
        user = User.objects.get(email=user.email)
        self.assertTrue(check_password(old_password, user.password))


class ChangePasswordConfirmHandlerTest(TestCase):

    def check_success(self, confirm_obj: Union[ConfirmEmail, ConfirmPhone], obj_confirm: ObjConfirm):
        old_password = faker.password()
        create_user_data = {'email': confirm_obj.email} if isinstance(confirm_obj, ConfirmEmail) else \
            {'phone': confirm_obj.phone}

        user = create_base_user(**create_user_data, password=old_password)
        new_password = faker.password()

        handlers.change_password_by_confirm(confirm_obj.secret_code, new_password, new_password, obj_confirm)

        user_filter = {'email': user.email} if isinstance(confirm_obj, ConfirmEmail) else {'phone': user.phone}
        user = User.objects.get(**user_filter)
        self.assertFalse(check_password(old_password, user.password))
        self.assertTrue(check_password(new_password, user.password))

        if isinstance(confirm_obj, ConfirmEmail):
            confirm_obj = ConfirmEmail.objects.filter(email=confirm_obj.email)
        else:
            confirm_obj = ConfirmPhone.objects.filter(phone=confirm_obj.phone)

        self.assertFalse(confirm_obj.exists())

    def check_fail(self, secret_code: uuid.UUID, obj_confirm: ObjConfirm, exception, confirm_password=None):
        password = faker.password()
        if confirm_password is None:
            confirm_password = password
        with self.assertRaises(exception):
            handlers.change_password_by_confirm(
                secret_code, password, confirm_password, obj_confirm
            )

    def test_success(self):
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        self.check_success(confirm_obj, ObjConfirm.EMAIL)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        self.check_success(confirm_obj, ObjConfirm.PHONE)

    def test_fail(self):
        # Пароли не совпадают
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        self.check_fail(confirm_obj.secret_code, ObjConfirm.EMAIL, exceptions.PasswordNotEqual, faker.password())

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        self.check_fail(confirm_obj.secret_code, ObjConfirm.PHONE, exceptions.PasswordNotEqual, faker.password())

        # Передан не существующий secret_code
        # EMAIL
        self.check_fail(uuid.uuid4(), ObjConfirm.EMAIL, exceptions.ConfirmObjNotFound)

        # PHONE
        self.check_fail(uuid.uuid4(), ObjConfirm.PHONE, exceptions.ConfirmObjNotFound)

        # Объект подтверждения email не подтвержден
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=False, type_confirm=TypeConfirm.RESET_PASS)
        self.check_fail(confirm_obj.secret_code, ObjConfirm.EMAIL, exceptions.ConfirmObjNotConfirmed)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=False, type_confirm=TypeConfirm.RESET_PASS)
        self.check_fail(confirm_obj.secret_code, ObjConfirm.PHONE, exceptions.ConfirmObjNotConfirmed)

        # Неверный тип объекта подтверждения
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        self.check_fail(confirm_obj.secret_code, ObjConfirm.EMAIL, exceptions.ConfirmObjNotFound)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        self.check_fail(confirm_obj.secret_code, ObjConfirm.PHONE, exceptions.ConfirmObjNotFound)

        # Отсутствует пользователь с email для смены пароля
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        self.check_fail(confirm_obj.secret_code, ObjConfirm.EMAIL, exceptions.UserNotFound)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.RESET_PASS)
        self.check_fail(confirm_obj.secret_code, ObjConfirm.PHONE, exceptions.UserNotFound)

