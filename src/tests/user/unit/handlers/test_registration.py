import uuid

from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.test import TestCase
from faker import Faker

import exceptions
import user.handlers.registration as handlers
from confirm.choices import TypeConfirm, ObjConfirm
from confirm.models import ConfirmEmail, ConfirmPhone
from tests.confirm.factories import ConfirmEmailFactory, ConfirmPhoneFactory
from tests.utils import create_base_user
from user.models import User, UserGroup
from typing import Union

faker = Faker()


class RegistrationHandlerTest(TestCase):
    def check_success(self, confirm_obj: Union[ConfirmEmail, ConfirmPhone], password):
        if isinstance(confirm_obj, ConfirmEmail):
            user_filter = {'email': confirm_obj.email}
        else:
            user_filter = {'phone': confirm_obj.phone}

        user = User.objects.filter(is_superuser=False, **user_filter)
        self.assertTrue(user.exists())

        user = user.get()

        self.assertTrue(check_password(password, user.password))

        user_group = user.groups.filter(name=UserGroup.BASE)
        self.assertTrue(user_group.exists())

        if isinstance(confirm_obj, ConfirmEmail):
            confirm_obj = ConfirmEmail.objects.filter(email=confirm_obj.email)
        else:
            confirm_obj = ConfirmPhone.objects.filter(phone=confirm_obj.phone)

        self.assertFalse(confirm_obj.exists())

    def fail_check_data(self, confirm_obj: Union[ConfirmEmail, ConfirmPhone]):
        if isinstance(confirm_obj, ConfirmEmail):
            user_filter = {'email': confirm_obj.email}
        else:
            user_filter = {'phone': confirm_obj.phone}

        user = User.objects.filter(is_superuser=False, **user_filter)
        self.assertFalse(user.exists())

        group = Group.objects.filter(name=UserGroup.BASE)
        self.assertFalse(group.exists())

        if isinstance(confirm_obj, ConfirmEmail):
            confirm_obj = ConfirmEmail.objects.filter(email=confirm_obj.email)
        else:
            confirm_obj = ConfirmPhone.objects.filter(phone=confirm_obj.phone)

        self.assertTrue(confirm_obj.exists())

    def test_success_registration(self):
        password = faker.password()

        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        handlers.registration(confirm_obj.secret_code, password, password, ObjConfirm.EMAIL)
        self.check_success(confirm_obj, password)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        handlers.registration(confirm_obj.secret_code, password, password, ObjConfirm.PHONE)
        self.check_success(confirm_obj, password)

    def test_fail(self):
        password = faker.password()

        # Переданы разные пароли
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        with self.assertRaises(exceptions.PasswordNotEqual):
            handlers.registration(confirm_obj.secret_code, faker.password(), faker.password(), ObjConfirm.EMAIL)
        self.fail_check_data(confirm_obj)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        with self.assertRaises(exceptions.PasswordNotEqual):
            handlers.registration(confirm_obj.secret_code, faker.password(), faker.password(), ObjConfirm.PHONE)
        self.fail_check_data(confirm_obj)

        # Передан неверный секретный код
        # EMAIL
        with self.assertRaises(exceptions.ConfirmObjNotFound):
            handlers.registration(uuid.uuid4(), password, password, ObjConfirm.EMAIL)

        # PHONE
        with self.assertRaises(exceptions.ConfirmObjNotFound):
            handlers.registration(uuid.uuid4(), password, password, ObjConfirm.PHONE)

        # Секретный код не подтвержден
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=False)
        with self.assertRaises(exceptions.ConfirmObjNotConfirmed):
            handlers.registration(confirm_obj.secret_code, password, password, ObjConfirm.EMAIL)
        self.fail_check_data(confirm_obj)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=False)
        with self.assertRaises(exceptions.ConfirmObjNotConfirmed):
            handlers.registration(confirm_obj.secret_code, password, password, ObjConfirm.PHONE)
        self.fail_check_data(confirm_obj)

        # Секретный код не для регистрации
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        with self.assertRaises(exceptions.ConfirmObjNotFound):
            handlers.registration(confirm_obj.secret_code, password, password, ObjConfirm.EMAIL)
        self.fail_check_data(confirm_obj)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        with self.assertRaises(exceptions.ConfirmObjNotFound):
            handlers.registration(confirm_obj.secret_code, password, password, ObjConfirm.PHONE)
        self.fail_check_data(confirm_obj)

        # Пользователь с таким email уже есть в системе
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        create_base_user(email=confirm_obj.email)
        with self.assertRaises(exceptions.UserAlreadyExist):
            handlers.registration(confirm_obj.secret_code, password, password, ObjConfirm.EMAIL)
        confirm_obj = ConfirmEmail.objects.filter(email=confirm_obj.email)
        self.assertFalse(confirm_obj.exists())

        # Пользователь с таким phone уже есть в системе
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        create_base_user(phone=confirm_obj.phone)
        with self.assertRaises(exceptions.UserAlreadyExist):
            handlers.registration(confirm_obj.secret_code, password, password, ObjConfirm.PHONE)
        confirm_obj = ConfirmPhone.objects.filter(phone=confirm_obj.phone)
        self.assertFalse(confirm_obj.exists())
