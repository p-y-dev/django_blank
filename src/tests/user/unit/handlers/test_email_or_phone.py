import uuid

from django.test import TestCase
from faker import Faker

import exceptions
import user.handlers.email_or_phone as handlers
from confirm.choices import TypeConfirm, ObjConfirm
from confirm.models import ConfirmEmail, ConfirmPhone
from tests.confirm.factories import ConfirmEmailFactory, ConfirmPhoneFactory
from tests.utils import create_base_user, rand_mobile_phone
from user.models import User
from typing import Union

faker = Faker()


class ChangeEmailOrPhoneHandlerTest(TestCase):
    def check_success(self, confirm_obj: Union[ConfirmEmail, ConfirmPhone], user: User, obj_confirm: ObjConfirm):
        handlers.change_email_or_phone(confirm_obj.secret_code, user, obj_confirm)

        user = User.objects.get(id=user.id)
        if isinstance(confirm_obj, ConfirmEmail):
            self.assertEqual(user.email, confirm_obj.email)
            confirm_obj = ConfirmEmail.objects.filter(email=confirm_obj.email)
            self.assertFalse(confirm_obj.exists())
        else:
            self.assertEqual(user.phone, confirm_obj.phone)
            confirm_obj = ConfirmPhone.objects.filter(phone=confirm_obj.phone)
            self.assertFalse(confirm_obj.exists())

    def check_fail(self, secret_code: uuid.UUID, change_user: User, obj_confirm: ObjConfirm, exception):
        with self.assertRaises(exception):
            handlers.change_email_or_phone(secret_code, change_user, obj_confirm)

        if obj_confirm == ObjConfirm.EMAIL:
            old_email = change_user.email
            user = User.objects.get(id=change_user.id)
            self.assertEqual(user.email, old_email)
        else:
            old_phone = change_user.phone
            user = User.objects.get(id=change_user.id)
            self.assertEqual(user.phone, old_phone)

    def test_success(self):
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        user = create_base_user(email=faker.email())
        self.check_success(confirm_obj, user, ObjConfirm.EMAIL)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        user = create_base_user(phone=rand_mobile_phone()['phone'])
        self.check_success(confirm_obj, user, ObjConfirm.PHONE)

    def test_fail(self):
        user = create_base_user(email=faker.email(), phone=rand_mobile_phone()['phone'])

        # Передан не существующий secret_code
        # EMAIL
        self.check_fail(uuid.uuid4(), user, ObjConfirm.EMAIL, exceptions.ConfirmObjNotFound)

        # PHONE
        self.check_fail(uuid.uuid4(), user, ObjConfirm.PHONE, exceptions.ConfirmObjNotFound)

        # Объект подтверждения не подтвержден
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=False, type_confirm=TypeConfirm.CHANGE)
        self.check_fail(confirm_obj.secret_code, user, ObjConfirm.EMAIL, exceptions.ConfirmObjNotConfirmed)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=False, type_confirm=TypeConfirm.CHANGE)
        self.check_fail(confirm_obj.secret_code, user, ObjConfirm.PHONE, exceptions.ConfirmObjNotConfirmed)

        # Объект подтверждения не типа CHANGE
        # EMAIL
        confirm_obj = ConfirmEmailFactory(confirmed=True)
        self.check_fail(confirm_obj.secret_code, user, ObjConfirm.EMAIL, exceptions.ConfirmObjNotFound)

        # PHONE
        confirm_obj = ConfirmPhoneFactory(confirmed=True)
        self.check_fail(confirm_obj.secret_code, user, ObjConfirm.PHONE, exceptions.ConfirmObjNotFound)

        # Пользователь с таки email есть в системе
        confirm_obj = ConfirmEmailFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        user = create_base_user(email=confirm_obj.email)
        self.check_fail(confirm_obj.secret_code, user, ObjConfirm.EMAIL, exceptions.UserAlreadyExist)
        confirm_obj = ConfirmEmail.objects.filter(id=confirm_obj.id)
        self.assertFalse(confirm_obj.exists())

        # Пользователь с таки номером есть в системе
        confirm_obj = ConfirmPhoneFactory(confirmed=True, type_confirm=TypeConfirm.CHANGE)
        user = create_base_user(phone=confirm_obj.phone)
        self.check_fail(confirm_obj.secret_code, user, ObjConfirm.PHONE, exceptions.UserAlreadyExist)
        confirm_obj = ConfirmPhone.objects.filter(id=confirm_obj.id)
        self.assertFalse(confirm_obj.exists())
