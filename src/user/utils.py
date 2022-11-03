from rest_framework_simplejwt.tokens import RefreshToken
from user.models import User
import exceptions


def get_jwt_tokens(user: User) -> dict:
    """
    Получение jwt токенов для пользователя
    :param user: Объект пользователя авторизации
    :return: Словарь с jwt токенами
        - access str - jwt токен доступа
        - refresh str - jwt токен обновления
    """

    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def passwd_is_equal(password: str, confirm_password: str):
    """
    Проверка незашифрованных паролей
    """

    if password != confirm_password:
        raise exceptions.PasswordNotEqual
