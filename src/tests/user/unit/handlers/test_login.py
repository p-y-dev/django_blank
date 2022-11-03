from django.test import TestCase
from faker import Faker

import exceptions
import user.handlers.login as handlers
from tests.utils import create_base_user, jwt_decode, rand_mobile_phone
from confirm.choices import PhoneRegion

faker = Faker()


class LoginByEmailHandler(TestCase):
    def check_success(self, user_id, email, password):
        jwt_tokens = handlers.login_by_email(email, password)
        self.assertIn('access', jwt_tokens)
        self.assertIn('refresh', jwt_tokens)
        jwt_data = jwt_decode(jwt_tokens['access'])
        self.assertEqual(jwt_data['user_id'], user_id)

    def test_success_login(self):
        password = faker.password()
        user = create_base_user(email=faker.email(), password=password)
        self.check_success(user.id, user.email, password)
        self.check_success(user.id, user.email.upper(), password)

    def test_fail_login(self):
        # Передан неверный email
        password = faker.password()
        create_base_user(email=faker.email(), password=password)
        with self.assertRaises(exceptions.UserNotFound):
            handlers.login_by_email(faker.email(), password)

        # Передан неверный пароль
        email = faker.email()
        create_base_user(email=email, password=faker.password())
        with self.assertRaises(exceptions.UserNotFound):
            handlers.login_by_email(email, faker.password())


class LoginByPhoneHandler(TestCase):
    def check_success(self, user_id, phone, region, password):
        jwt_tokens = handlers.login_by_phone(phone, region, password)
        self.assertIn('access', jwt_tokens)
        self.assertIn('refresh', jwt_tokens)
        jwt_data = jwt_decode(jwt_tokens['access'])
        self.assertEqual(jwt_data['user_id'], user_id)

    def test_success_login(self):
        password = faker.password()
        phone = rand_mobile_phone()
        user = create_base_user(phone=phone['phone'], password=password)
        self.check_success(user.id, phone['number'], PhoneRegion.RUSSIAN, password)

    def test_fail_login(self):

        # Передан некорректный номер телефона
        with self.assertRaises(exceptions.IncorrectPhone):
            handlers.login_by_phone('234da', PhoneRegion.RUSSIAN, faker.password())

        password = faker.password()
        phone = rand_mobile_phone()
        create_base_user(phone=phone['phone'], password=password)

        # Передан неверный телефон
        with self.assertRaises(exceptions.UserNotFound):
            handlers.login_by_phone(rand_mobile_phone()['number'], PhoneRegion.RUSSIAN, password)

        # Передан неверный пароль
        with self.assertRaises(exceptions.UserNotFound):
            handlers.login_by_phone(phone['number'], PhoneRegion.RUSSIAN, faker.password())
