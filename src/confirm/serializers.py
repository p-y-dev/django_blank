from django.conf import settings
from rest_framework import serializers

from confirm.choices import TypeConfirm, ObjConfirm, PhoneRegion


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(label='email')

    @staticmethod
    def validate_email(obj):
        return obj.lower()


class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(help_text='Номер телефона(без кода)')
    region = serializers.ChoiceField(
        choices=PhoneRegion.choices,
        help_text='Регион номера телефона'
    )


class BaseConfirmSerializer(serializers.Serializer):
    type_confirm = serializers.ChoiceField(
        choices=TypeConfirm.choices,
        help_text='Тип подтверждения'
    )


class CreateConfirmEmailSerializer(BaseConfirmSerializer, EmailSerializer):
    pass


class EmailSecretCodeSerializer(serializers.Serializer):
    secret_code = serializers.CharField(max_length=1024)


class CreateConfirmPhoneSerializer(BaseConfirmSerializer, PhoneSerializer):
    pass


class PhoneSecretCodeSerializer(serializers.Serializer):
    secret_code = serializers.CharField(max_length=1024)
    sec_resend = serializers.IntegerField(label='Количество секунд для повторной отправки')
    count_resend = serializers.IntegerField(label='Количество доступных повторных отправок')


class ConfirmSerializer(serializers.Serializer):
    secret_code = serializers.UUIDField()
    confirm_code = serializers.CharField(
        min_length=settings.LENGTH_CONFIRM_CODE, max_length=settings.LENGTH_CONFIRM_CODE
    )
    object_confirm = serializers.ChoiceField(
        choices=ObjConfirm.choices,
        help_text='Объект подтверждения'
    )