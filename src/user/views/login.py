from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

import exceptions
import http_exceptions
import user.handlers.login as handlers
from user import serializers


@swagger_auto_schema(
    method='post',
    operation_id='login_by_email',
    operation_summary='Авторизация по email.',
    request_body=serializers.LoginByEmailSerializer,
    responses={
        status.HTTP_200_OK: serializers.LoginResponseSerializer()
    }
)
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def login_by_email(request):
    serializer = serializers.LoginByEmailSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        jwt_token_data = handlers.login_by_email(
            serializer.validated_data['email'],
            serializer.validated_data['password']
        )
    except exceptions.UserNotFound as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    return Response(
        serializers.LoginResponseSerializer(jwt_token_data).data,
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method='post',
    operation_id='login_by_phone',
    operation_summary='Авторизация по phone.',
    request_body=serializers.LoginByPhoneSerializer,
    responses={
        status.HTTP_200_OK: serializers.LoginResponseSerializer()
    }
)
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def login_by_phone(request):
    serializer = serializers.LoginByPhoneSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        jwt_token_data = handlers.login_by_phone(
            serializer.validated_data['phone'],
            serializer.validated_data['region'],
            serializer.validated_data['password']
        )
    except (exceptions.UserNotFound, exceptions.IncorrectPhone) as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    return Response(
        serializers.LoginResponseSerializer(jwt_token_data).data,
        status=status.HTTP_200_OK
    )
