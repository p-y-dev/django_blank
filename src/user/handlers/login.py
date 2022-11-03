from user.models import User
import exceptions
from django.contrib.auth.hashers import check_password
from user.utils import get_jwt_tokens
from confirm.utils import normalization_phone_number
from confirm.choices import PhoneRegion


def login_by_email(email: str, password: str) -> dict:
    """
    Логин пользователя по email
    :param email: Email пользователя
    :param password: Пароль пользователя
    :return: Словарь содержащий jwt токены
    """

    email = email.lower()

    user = User.objects.filter(email=email)
    if not user.exists():
        raise exceptions.UserNotFound
    user = user.get()

    if not check_password(password, user.password):
        raise exceptions.UserNotFound

    return get_jwt_tokens(user)


def login_by_phone(phone: str, region: PhoneRegion, password: str) -> dict:
    """
    Логин пользователя по email
    :param phone: Номер телефона пользователя без кода страны
    :param region: Регион номера телефона ISO 3166-1 Alpha-2
    :param password: Пароль пользователя
    :return: Словарь содержащий jwt токены
    """

    phone = normalization_phone_number(phone, region)

    user = User.objects.filter(phone=phone)
    if not user.exists():
        raise exceptions.UserNotFound
    user = user.get()

    if not check_password(password, user.password):
        raise exceptions.UserNotFound

    return get_jwt_tokens(user)
