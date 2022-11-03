import jwt
from django.conf import settings
from django.test import TestCase
from faker import Faker

import exceptions
from tests.utils import create_base_user, jwt_decode
from user import utils

faker = Faker()


class UserUtilsTest(TestCase):
    def test_get_jwt_tokens(self):
        user = create_base_user(email=faker.email())
        access_token = utils.get_jwt_tokens(user)['access']
        jwt_data = jwt_decode(access_token)
        self.assertEqual(jwt_data['user_id'], user.id)

    def test_passwd_is_equal(self):
        # Пароли равны
        password = 'Adwd323fdasef'
        confirm_password = password
        utils.passwd_is_equal(password, confirm_password)

        # Пароли не равны
        confirm_password = '9daj3oiJofsf9'
        with self.assertRaises(exceptions.PasswordNotEqual):
            utils.passwd_is_equal(password, confirm_password)

