from uuid import UUID

from django.contrib.auth.hashers import make_password
from django.db import transaction

import exceptions
from confirm.choices import TypeConfirm, ObjConfirm
from confirm.models import ConfirmEmail, ConfirmPhone
from user.models import User
from user.utils import passwd_is_equal


def change_password(user: User, password: str, confirm_password: str):
    """
    Изменение пароля

    :param user: Объект пользователя у которого нужно изменить пароль
    :param password: Пароль
    :param confirm_password: Подтверждение пароля
    """

    passwd_is_equal(password, confirm_password)
    user.password = make_password(password)
    user.save()


def change_password_by_confirm(secret_code: UUID, password: str, confirm_password: str, object_confirm: ObjConfirm):
    """
    Изменение пароля, через объект подтверждения

    :param secret_code: Секретный код объекта подтверждения
    :param password: Пароль
    :param confirm_password: Подтверждение пароля
    :param object_confirm: Тип объекта подтверждения
    """

    passwd_is_equal(password, confirm_password)

    if object_confirm == ObjConfirm.EMAIL:
        confirm_obj = ConfirmEmail.objects.get_confirmed(secret_code, TypeConfirm.RESET_PASS)
        user_fiter_data = {'email': confirm_obj.email}
    else:
        confirm_obj = ConfirmPhone.objects.get_confirmed(secret_code, TypeConfirm.RESET_PASS)
        user_fiter_data = {'phone': confirm_obj.phone}

    user = User.objects.filter(**user_fiter_data)
    if not user.exists():
        confirm_obj.delete()
        raise exceptions.UserNotFound

    with transaction.atomic():
        user.update(password=make_password(password))
        confirm_obj.delete()
