from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

import exceptions
import http_exceptions
import user.handlers.email_or_phone as handlers
from user.permissions import user_group_permission
from user import serializers


@swagger_auto_schema(
    method='patch',
    operation_id='change_email_or_phone',
    operation_summary='Изменение email или телефона.',
    operation_description='Bearer AUTH',
    request_body=serializers.ChangeEmailPhoneSerializer,
    responses={status.HTTP_204_NO_CONTENT: ''}
)
@api_view(['PATCH'])
@permission_classes([user_group_permission(None)])
def change(request):
    serializer = serializers.ChangeEmailPhoneSerializer(data=request.data)
    if not serializer.is_valid():
        raise http_exceptions.Validate(validation_errors=serializer.errors)

    try:
        handlers.change_email_or_phone(
            serializer.validated_data['secret_code'],
            request.user,
            serializer.validated_data['object_confirm'],
        )
    except (
            exceptions.ConfirmObjNotConfirmed,
            exceptions.ConfirmObjNotFound,
            exceptions.UserAlreadyExist
    ) as e:
        raise http_exceptions.Conflict(detail=e.message, code=e.code)

    return Response(status=status.HTTP_204_NO_CONTENT)
