from django.urls import reverse
from faker import Faker
from rest_framework import status

import exceptions
from confirm.choices import PhoneRegion
from tests.utils import BaseE2ETest, create_base_user, rand_mobile_phone

faker = Faker()


class LoginByEmailE2ETest(BaseE2ETest):
    def setUp(self):
        self.url = reverse('user:login_by_email')

    def test_success(self):
        password = faker.password()
        email = faker.email()

        create_base_user(email=email, password=password)

        request_data = {'email': email, 'password': password}
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_200_OK)

        response_data = response_data.json()
        self.assertIn('access', response_data)
        self.assertIn('refresh', response_data)

    def test_fail(self):
        # Передан неверный email
        password = faker.password()
        create_base_user(email=faker.email(), password=password)
        request_data = {'email': faker.email(), 'password': password}
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserNotFound)

        # Передан неверный пароль
        email = faker.email()
        create_base_user(email=email, password=faker.password())
        request_data = {'email': email, 'password': faker.password()}
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserNotFound)


class LoginByPhoneE2ETest(BaseE2ETest):
    def setUp(self):
        self.url = reverse('user:login_by_phone')

    def test_success(self):
        password = faker.password()
        phone = rand_mobile_phone()
        create_base_user(phone=phone['phone'], password=password)

        request_data = {'phone': phone['number'], 'region': PhoneRegion.RUSSIAN, 'password': password}
        response_data = self.client.post(self.url, request_data)
        self.assertEqual(response_data.status_code, status.HTTP_200_OK)

        response_data = response_data.json()
        self.assertIn('access', response_data)
        self.assertIn('refresh', response_data)

    def test_fail(self):
        # Передан некорректный телефон
        password = faker.password()
        number_phone = '923456'
        request_data = {'phone': number_phone, 'region': PhoneRegion.RUSSIAN, 'password': password}
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.IncorrectPhone)

        # Пользователя не существует с таки номером телефона
        password = faker.password()
        request_data = {'phone': rand_mobile_phone()['number'], 'region': PhoneRegion.RUSSIAN, 'password': password}
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserNotFound)

        # Передан неверный пароль
        phone = rand_mobile_phone()
        create_base_user(phone=phone['phone'], password=password)
        request_data = {'phone': phone['number'], 'region': PhoneRegion.RUSSIAN, 'password': 'ADaw323dawd'}
        response_data = self.client.post(self.url, request_data)
        self.conflict_response(response_data, exceptions.UserNotFound)
