from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from confirm.choices import TypeConfirm
from confirm.managers import ConfirmEmailManager, ConfirmPhoneManager


class BaseConfirmation(models.Model):
    secret_code = models.UUIDField(verbose_name=_('Секретный код'), unique=True)
    confirm_code = models.CharField(verbose_name=_('Код подтверждения'), max_length=128)
    created_at = models.DateTimeField(verbose_name=_('Дата создания кода подтверждения'))
    confirmed = models.BooleanField(verbose_name=_('Подтвержден?'))
    type_confirm = models.CharField(verbose_name=_('Тип'), choices=TypeConfirm.choices, max_length=16)

    class Meta:
        abstract = True


class ConfirmEmail(BaseConfirmation):
    email = models.EmailField(verbose_name=_('Email'), unique=True)
    objects = ConfirmEmailManager()

    class Meta:
        verbose_name = _('Подтверждение email')
        verbose_name_plural = _('Подтверждения emails')

    def __str__(self):
        return f'{self.email}'

    @property
    def is_expired(self) -> bool:
        ttl_hours = settings.EMAIL_VER_TTL_HOURS
        if self.created_at + timezone.timedelta(hours=ttl_hours) < timezone.now():
            return True

        return False


class ConfirmPhone(BaseConfirmation):
    phone = PhoneNumberField(verbose_name=_('Телефон'), unique=True)
    count_send = models.PositiveIntegerField(verbose_name='Количество отправок', default=1)
    objects = ConfirmPhoneManager()

    class Meta:
        verbose_name = _('Подтверждение телефона')
        verbose_name_plural = _('Подтверждения телефонов')

    def __str__(self):
        return f'{self.phone}'

    @property
    def sec_resend(self) -> int:
        """
        Количество оставшихся секунд для последующей отправки кода подтверждения, если есть еще попытки
        """

        if self.count_resend <= 0:
            return 0

        count_sec_resend = settings.PHONE_CONFIRM_STEP_WAITING_SECONDS * self.count_send
        passed_seconds_after_sending = int((timezone.now() - self.created_at).total_seconds())
        count_sec = count_sec_resend - passed_seconds_after_sending
        return 0 if count_sec < 0 else count_sec

    @property
    def count_resend(self) -> int:
        """
        Количество попыток для отправки кода подтверждения
        """

        return settings.PHONE_CONFIRM_CODE_COUNT_SEND - self.count_send

    @property
    def count_sec_wait_renewal_sending(self) -> int:
        """
        Сколько секунд нужно ждать, для сброса попыток на отправку
        """

        passed_seconds_after_sending = int((timezone.now() - self.created_at).total_seconds())
        count_sec = settings.PHONE_CONFIRM_RESET_COUNT_SEND_SECONDS - passed_seconds_after_sending
        return 0 if count_sec < 0 else count_sec

    @property
    def is_expired(self) -> bool:
        ttl_hours = settings.PHONE_VER_TTL_HOURS
        if self.created_at + timezone.timedelta(hours=ttl_hours) < timezone.now():
            return True

        return False
