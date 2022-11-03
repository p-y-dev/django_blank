import random

import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from faker import Faker
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.test import APITestCase

from tests.user.factories import UserFactory
from user.models import UserGroup, User
from user.utils import get_jwt_tokens

faker = Faker()


class BaseE2ETest(APITestCase):
    def conflict_response(self, response_data, exception_class):
        self.assertEqual(response_data.status_code, status.HTTP_409_CONFLICT)

        response_data = response_data.json()

        exc = exception_class()
        self.assertEqual(response_data['detail'], exc.message)
        self.assertEqual(response_data['code'], exc.code)

    def unauthorized_response(self, response_data):
        self.assertEqual(response_data.status_code, status.HTTP_401_UNAUTHORIZED)
        response_data = response_data.json()
        exc = NotAuthenticated()
        self.assertEqual(response_data['detail'], exc.default_detail)
        self.assertEqual(response_data['code'], exc.__class__.__name__)

    def set_bearer_credentials(self, user: User):
        jwt_token = get_jwt_tokens(user)['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_token}')


def jwt_decode(access_token: str):
    return jwt.decode(
        access_token,
        settings.SIMPLE_JWT['SIGNING_KEY'],
        algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
    )


def create_user(**kwargs):
    if kwargs.get('email') is None and kwargs.get('phone') is None:
        raise ValueError('Укажите email или phone')

    password = kwargs.pop('password', None)
    if password is None:
        password = faker.password()

    password = make_password(password)
    user = UserFactory(password=password, **kwargs)
    return user


def create_base_user(**kwargs) -> User:
    user = create_user(**kwargs)
    base_group = Group.objects.get_or_create(name=UserGroup.BASE)[0]
    user.groups.add(base_group)
    return user


def rand_mobile_phone():
    number = ''
    for x in range(7):
        number = number + random.choice(list('123456789'))

    code = random.choice([
        '911', '912', '917', '919', '904', '922',
        '929', '931', '932', '937', '939', '999',
        '900', '901', '902', '904', '908', '950',
        '951', '952', '953', '991', '992'
    ])

    return {
        'phone': f'+7{code}{number}',
        'number': f'{code}{number}'
    }
