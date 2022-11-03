from django.utils.translation import gettext_lazy as _


class BaseException(Exception):
    code = None


class UserAlreadyExist(BaseException):
    def __init__(self):
        self.message = _('Пользователь уже существует')
        self.code = self.__class__.__name__


class UserNotFound(BaseException):
    def __init__(self):
        self.message = _('Пользователь не найден')
        self.code = self.__class__.__name__


class ConfirmObjNotFound(BaseException):
    def __init__(self):
        self.message = _('Объект подтверждения не найден')
        self.code = self.__class__.__name__


class ConfirmObjNotConfirmed(BaseException):
    def __init__(self):
        self.message = _('Объект подтверждения не подтвержден')
        self.code = self.__class__.__name__


class ConfirmCodeExpired(BaseException):
    def __init__(self):
        self.message = _('Время подтверждения истекло')
        self.code = self.__class__.__name__


class PasswordNotEqual(BaseException):
    def __init__(self):
        self.message = _('Пароли не равны')
        self.code = self.__class__.__name__


class IncorrectPhone(BaseException):
    def __init__(self):
        self.message = _('Некорректный номер телефона')
        self.code = self.__class__.__name__


class ConfirmPhoneExcMaxCountSend(BaseException):
    def __init__(self, count_sec: int):
        self.message = _('Превышено максимальное количество отправок кода на номер, попробуйте позже')
        self.code = self.__class__.__name__
        self.payload_data = {'wait_seconds': count_sec}


class ConfirmPhoneWaitBeforeSending(BaseException):
    def __init__(self, count_sec: int):
        self.message = _(f'Отправить код подтверждения невозможно, попробуйте позже')
        self.code = self.__class__.__name__
        self.payload_data = {'wait_seconds': count_sec}
