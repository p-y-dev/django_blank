from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

import exceptions
import http_exceptions
from confirm import handlers, serializers
from notification.emails.tasks import task_send_confirm_code_email
from notification.sms.tasks import task_send_confirm_code_phone


@swagger_auto_schema(
    method='post',
    operation_id='create_confirm_email',
    operation_summary='Создание кода подтверждения email.',
    request_body=serializers.CreateConfirmEmailSerializer,
    responses={
        status.HTTP_201_CREATED: serializers.EmailSecretCodeSerializer()
    }
)
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def create_confirm_email(request):
    serializer = serializers.CreateConfirmEmailSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        confirm_email = handlers.create_confirm_email(
            serializer.validated_data['email'], serializer.validated_data['type_confirm']
        )
    except (exceptions.UserAlreadyExist, exceptions.UserNotFound) as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    task_send_confirm_code_email.delay(confirm_email.email, confirm_email.confirm_code)

    return Response(serializers.EmailSecretCodeSerializer(confirm_email).data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    operation_id='create_confirm_phone',
    operation_summary='Создание кода подтверждения phone.',
    request_body=serializers.CreateConfirmPhoneSerializer,
    responses={
        status.HTTP_201_CREATED: serializers.PhoneSecretCodeSerializer()
    }
)
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def create_confirm_phone(request):
    serializer = serializers.CreateConfirmPhoneSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        confirm_phone = handlers.create_confirm_phone(
            serializer.validated_data['phone'],
            serializer.validated_data['region'],
            serializer.validated_data['type_confirm']
        )

    except (
            exceptions.ConfirmPhoneWaitBeforeSending,
            exceptions.ConfirmPhoneExcMaxCountSend
    ) as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code, payload_data=e.payload_data)

    except (
            exceptions.IncorrectPhone,
            exceptions.UserAlreadyExist,
            exceptions.UserNotFound,
    ) as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    task_send_confirm_code_phone.delay(confirm_phone.phone.as_e164, confirm_phone.confirm_code)

    return Response(serializers.PhoneSecretCodeSerializer(confirm_phone).data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    operation_id='confirm_phone',
    operation_summary='Подтверждения email или phone.',
    request_body=serializers.ConfirmSerializer,
    responses={
        status.HTTP_204_NO_CONTENT: ''
    }
)
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def confirm(request):
    serializer = serializers.ConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        handlers.confirm_obj(
            serializer.validated_data['secret_code'],
            serializer.validated_data['confirm_code'],
            serializer.validated_data['object_confirm'],
        )
    except (exceptions.ConfirmObjNotFound, exceptions.ConfirmCodeExpired) as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    return Response(status=status.HTTP_204_NO_CONTENT)
