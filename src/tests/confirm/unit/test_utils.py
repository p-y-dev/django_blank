from uuid import UUID

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from confirm import utils
from confirm.choices import TypeConfirm, PhoneRegion
from tests.utils import create_user
import exceptions
from faker import Faker

faker = Faker()


class ConfirmUtilsTest(TestCase):
    def test_generate_confirm_code(self):
        """
        Проверка генерации кода подтверждения
        """

        confirm_code = utils.generate_confirm_code()
        self.assertIsInstance(confirm_code, str)
        self.assertEqual(len(confirm_code), settings.LENGTH_CONFIRM_CODE)

    def test_generate_confirm_data(self):
        """
        Проверка генерации данных для создания кода подтверждения
        """
        confirm_data = utils.generate_confirm_data(TypeConfirm.REGISTRATION)
        self.assertIsInstance(confirm_data, dict)
        self.assertIsInstance(confirm_data['secret_code'], UUID)
        self.assertIsInstance(confirm_data['confirm_code'], str)
        self.assertIsInstance(confirm_data['type_confirm'], str)
        self.assertIsInstance(confirm_data['confirmed'], bool)
        self.assertIsInstance(confirm_data['created_at'], timezone.datetime)


class TypeConfirmIsAvailableForUserTest(TestCase):
    def check_fail(self, type_confirm, user_filter_data, exception):
        with self.assertRaises(exception):
            utils.type_confirm_is_available_for_user(type_confirm, user_filter_data)

    @staticmethod
    def test_success():
        # Фильтр по Email
        user_filter_data = {'email': faker.email()}
        utils.type_confirm_is_available_for_user(TypeConfirm.REGISTRATION, user_filter_data)
        utils.type_confirm_is_available_for_user(TypeConfirm.CHANGE, user_filter_data)

        email = faker.email()
        create_user(email=email)
        user_filter_data = {'email': email}
        utils.type_confirm_is_available_for_user(TypeConfirm.RESET_PASS, user_filter_data)

        # Фильтр по телефону
        user_filter_data = {'phone': '+79233334445'}
        utils.type_confirm_is_available_for_user(TypeConfirm.REGISTRATION, user_filter_data)
        utils.type_confirm_is_available_for_user(TypeConfirm.CHANGE, user_filter_data)

        phone = '+79232345683'
        create_user(phone=phone)
        user_filter_data = {'phone': phone}
        utils.type_confirm_is_available_for_user(TypeConfirm.RESET_PASS, user_filter_data)

    def test_fail(self):
        # Количество элементов фильтра пользователя != 1
        user_filter_data = {'phone': '=792324856', 'email': 'a@mail.ru'}
        self.check_fail(TypeConfirm.REGISTRATION, user_filter_data, ValueError)

        # В фильтр передан неверный ключ
        user_filter_data = {'adw': 'daw'}
        self.check_fail(TypeConfirm.REGISTRATION, user_filter_data, ValueError)

        email = faker.email()
        create_user(email=email)
        user_filter_data = {'email': email}
        self.check_fail(TypeConfirm.REGISTRATION, user_filter_data, exceptions.UserAlreadyExist)
        self.check_fail(TypeConfirm.CHANGE, user_filter_data, exceptions.UserAlreadyExist)
        user_filter_data = {'email': faker.email()}
        self.check_fail(TypeConfirm.RESET_PASS, user_filter_data, exceptions.UserNotFound)

        phone = '+79232345683'
        create_user(phone=phone)
        user_filter_data = {'phone': phone}
        self.check_fail(TypeConfirm.REGISTRATION, user_filter_data, exceptions.UserAlreadyExist)
        self.check_fail(TypeConfirm.CHANGE, user_filter_data, exceptions.UserAlreadyExist)
        user_filter_data = {'phone': '+79068974456'}
        self.check_fail(TypeConfirm.RESET_PASS, user_filter_data, exceptions.UserNotFound)


class NormalizationPhoneNumberTest(TestCase):
    def test_success(self):
        phone_number = '9234322345'
        phone = utils.normalization_phone_number(phone_number, PhoneRegion.RUSSIAN)
        self.assertEqual(f'+7{phone_number}', phone)

    def test_fail(self):
        phone_number = 'daw32332'
        with self.assertRaises(exceptions.IncorrectPhone):
            utils.normalization_phone_number(phone_number, PhoneRegion.RUSSIAN)
