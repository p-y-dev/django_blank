import random
import string
import uuid

from django.conf import settings
from django.utils import timezone
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers.phonenumberutil import NumberParseException

import exceptions
from confirm.choices import PhoneRegion
from confirm.choices import TypeConfirm
from user.models import User


def generate_confirm_code() -> str:
    """
    Генерация кода подтверждения

    :return: Код подтверждения
    """

    length = settings.LENGTH_CONFIRM_CODE
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def generate_confirm_data(type_confirm: TypeConfirm) -> dict:
    """
    Генерация данных для создания кода подтверждения

    :param type_confirm: Тип кода подтверждения
    :return: Словарь с данными кода подтверждения
        - secret_code uuid - секретный код
        - confirm_code str - код подтверждения
        - created_at timezone.datetime - дата и время создания
        - type_confirm TypeConfirm - тип подтверждения
        - confirmed bool - Подтвержден ли объект

    """

    return {
        'secret_code': uuid.uuid4(),
        'confirm_code': generate_confirm_code(),
        'created_at': timezone.now(),
        'confirmed': False,
        'type_confirm': type_confirm
    }


def type_confirm_is_available_for_user(type_confirm: TypeConfirm, user_filter_data: dict):
    """
    Проверка на то доступен ли тип подтверждения для дальнейшего его создания/обновления
    от наличия по пользователя в системе

    :param type_confirm: Тип подтверждения
    :param user_filter_data: Словарь, содержащий параметры, для поиска пользователя, например:
        - {'email': example@mail.ru} или {'phone': '+7xxxxxxxxxx'}

    """

    if len(user_filter_data.keys()) != 1:
        raise ValueError('Должен быть один элемент фильтра')

    if 'phone' not in user_filter_data and 'email' not in user_filter_data:
        raise ValueError('Параметр фильтра должен быть phone или email')

    user = User.objects.filter(**user_filter_data).exists()

    if type_confirm in [TypeConfirm.REGISTRATION, TypeConfirm.CHANGE] and user:
        raise exceptions.UserAlreadyExist

    if type_confirm == TypeConfirm.RESET_PASS and not user:
        raise exceptions.UserNotFound


def normalization_phone_number(phone: str, region: PhoneRegion) -> str:
    """
    Нормализация номера телефона для работы с бд

    :param phone: Номер телефона без кода страны
    :param region: Регион номера телефона ISO 3166-1 Alpha-2
    :return: Телефона в формате E164 преобразованный из номера и кода страны, например,
    если на вход подать phone - 9231234345 и region - RU, метод преобразует его к виду +79231234345
    """

    try:
        phone = PhoneNumber.from_string(phone, region=region)
    except NumberParseException:
        raise exceptions.IncorrectPhone

    if not phone.is_valid():
        raise exceptions.IncorrectPhone

    return phone.as_e164
