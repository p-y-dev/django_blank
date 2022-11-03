import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


class UserGroup(models.TextChoices):
    BASE = 'base'


class User(AbstractUser):
    password = models.CharField(_('Пароль'), max_length=128, null=True, default=None)
    username = models.CharField(verbose_name=_('Логин'), max_length=150, unique=True, default=uuid.uuid4)
    phone = PhoneNumberField(verbose_name=_('Телефон'), unique=True, null=True, default=None)
    email = models.EmailField(verbose_name=_('Email'), unique=True, null=True, default=None)

    created_at = models.DateTimeField(verbose_name=_('Дата создания'), default=timezone.now)
    updated_at = models.DateTimeField(verbose_name=_('Дата обновления'), default=timezone.now)

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-created_at']
