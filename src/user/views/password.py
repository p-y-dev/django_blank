from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

import exceptions
import http_exceptions
import user.handlers.password as handlers
from user.permissions import user_group_permission
from user import serializers


@swagger_auto_schema(
    method='patch',
    operation_id='change_password',
    operation_summary='Изменение пароля.',
    operation_description='Bearer AUTH',
    request_body=serializers.ChangePasswordSerializer,
    responses={status.HTTP_204_NO_CONTENT: ''}
)
@api_view(['PATCH'])
@permission_classes([user_group_permission(None)])
def change(request):
    serializer = serializers.ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        handlers.change_password(
            request.user,
            serializer.validated_data['password'],
            serializer.validated_data['confirm_password'],
        )
    except exceptions.PasswordNotEqual as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='patch',
    operation_id='change_password_by_confirm',
    operation_summary='Изменение пароля через код подтверждения.',
    request_body=serializers.ChangePasswordByConfirmSerializer,
    responses={status.HTTP_204_NO_CONTENT: ''}
)
@api_view(['PATCH'])
@authentication_classes([])
@permission_classes([])
def change_by_confirm(request):
    serializer = serializers.ChangePasswordByConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        handlers.change_password_by_confirm(
            serializer.validated_data['secret_code'],
            serializer.validated_data['password'],
            serializer.validated_data['confirm_password'],
            serializer.validated_data['object_confirm'],
        )
    except (
            exceptions.PasswordNotEqual,
            exceptions.UserNotFound,
            exceptions.ConfirmObjNotFound,
            exceptions.ConfirmObjNotConfirmed
    ) as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    return Response(status=status.HTTP_204_NO_CONTENT)
