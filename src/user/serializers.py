from django.conf import settings
from rest_framework import serializers

from confirm.choices import ObjConfirm
from confirm.serializers import EmailSerializer, PhoneSerializer


class BaseObjConfirmSerializer(serializers.Serializer):
    object_confirm = serializers.ChoiceField(
        choices=ObjConfirm.choices,
        help_text='Объект подтверждения'
    )


class PasswordSerializer(serializers.Serializer):
    password = serializers.RegexField(regex=settings.USER_REGEX_PASSWORD)
    confirm_password = serializers.RegexField(regex=settings.USER_REGEX_PASSWORD)


class LoginByEmailSerializer(EmailSerializer):
    password = serializers.CharField()


class LoginByPhoneSerializer(PhoneSerializer):
    password = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField(label='Токен доступа')
    refresh = serializers.CharField(label='Токен обновления')


class RegistraionSerializer(PasswordSerializer, BaseObjConfirmSerializer):
    secret_code = serializers.UUIDField()


class ChangePasswordSerializer(PasswordSerializer):
    pass


class ChangePasswordByConfirmSerializer(PasswordSerializer, BaseObjConfirmSerializer):
    secret_code = serializers.UUIDField()


class ChangeEmailPhoneSerializer(BaseObjConfirmSerializer):
    secret_code = serializers.UUIDField()
