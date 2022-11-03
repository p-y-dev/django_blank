from django.db import transaction

import exceptions
from confirm.choices import TypeConfirm, ObjConfirm
from confirm.models import ConfirmEmail, ConfirmPhone
from user.models import User
from uuid import UUID


def change_email_or_phone(secret_code: UUID, user_change: User, object_confirm: ObjConfirm):
    """
    Изменение у пользователя email или номера телефона после подтверждения

    :param secret_code: Секретный код объекта подтверждения
    :param user_change: Пользователь, который выполняет запрос на смену
    :param object_confirm: Тип объекта подтверждения
    """

    if object_confirm == ObjConfirm.EMAIL:
        confirm_obj = ConfirmEmail.objects.get_confirmed(secret_code, TypeConfirm.CHANGE)
        user_filter_data = {'email': confirm_obj.email}
    else:
        confirm_obj = ConfirmPhone.objects.get_confirmed(secret_code, TypeConfirm.CHANGE)
        user_filter_data = {'phone': confirm_obj.phone}

    if User.objects.filter(**user_filter_data).exists():
        confirm_obj.delete()
        raise exceptions.UserAlreadyExist

    with transaction.atomic():
        if isinstance(confirm_obj, ConfirmEmail):
            user_change.email = confirm_obj.email
        else:
            user_change.phone = confirm_obj.phone

        user_change.save()
        confirm_obj.delete()
