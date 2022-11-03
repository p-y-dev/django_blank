from uuid import UUID

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.db import transaction

import exceptions
from confirm.models import ConfirmEmail, ConfirmPhone
from confirm.choices import TypeConfirm, ObjConfirm
from user.models import User, UserGroup
from user.utils import passwd_is_equal


def registration(secret_code: UUID, password: str, confirm_password: str, object_confirm: ObjConfirm):
    """
    Регистрация пользователя в системе

    :param secret_code: Секретный код объекта подтверждения
    :param password: Пароль
    :param confirm_password: Подтверждение пароля
    :param object_confirm: Тип объекта подтверждения
    """
    passwd_is_equal(password, confirm_password)

    if object_confirm == ObjConfirm.PHONE:
        confirm_obj = ConfirmPhone.objects.get_confirmed(secret_code, TypeConfirm.REGISTRATION)
        user_data = {'phone': confirm_obj.phone}
    else:
        confirm_obj = ConfirmEmail.objects.get_confirmed(secret_code, TypeConfirm.REGISTRATION)
        user_data = {'email': confirm_obj.email}

    user = User.objects.filter(**user_data)
    if user.exists():
        confirm_obj.delete()
        raise exceptions.UserAlreadyExist

    base_group = Group.objects.get_or_create(name=UserGroup.BASE)[0]

    with transaction.atomic():
        user = User.objects.create(
            password=make_password(password),
            is_superuser=False,
            **user_data
        )
        user.groups.add(base_group)
        confirm_obj.delete()
