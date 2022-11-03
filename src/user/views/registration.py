from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

import exceptions
import http_exceptions
import user.handlers.registration as handlers
from user import serializers


@swagger_auto_schema(
    method='post',
    operation_id='registration',
    operation_summary='Регистрация.',
    request_body=serializers.RegistraionSerializer,
    responses={
        status.HTTP_204_NO_CONTENT: ''
    }
)
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def registration(request):
    serializer = serializers.RegistraionSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        handlers.registration(
            serializer.validated_data['secret_code'],
            serializer.validated_data['password'],
            serializer.validated_data['confirm_password'],
            serializer.validated_data['object_confirm'],
        )
    except (
            exceptions.PasswordNotEqual,
            exceptions.ConfirmObjNotFound,
            exceptions.UserAlreadyExist,
            exceptions.ConfirmObjNotConfirmed
    ) as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    return Response(status=status.HTTP_204_NO_CONTENT)
