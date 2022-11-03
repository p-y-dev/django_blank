from django.db import models


class TypeConfirm(models.TextChoices):
    REGISTRATION = 'registration'
    RESET_PASS = 'reset_pass'
    CHANGE = 'change'


class ObjConfirm(models.TextChoices):
    EMAIL = 'email'
    PHONE = 'phone'


class PhoneRegion(models.TextChoices):
    # ISO 3166-1 Alpha-2
    RUSSIAN = 'RU'
    UZBEKISTAN = 'UZ'
