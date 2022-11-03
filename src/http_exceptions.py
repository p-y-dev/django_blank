from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status, exceptions
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler, set_rollback


class BaseErrorResponse(APIException):
    """
        {
            'status': Дублирует код состояния HTTP
            'detail': Описание возникшей ошибки, или null
            'validation_errors': Список параметров и описание ошибок, возникших при валидации параметров запроса,
            или null
            'code': Код ошибки, нужен для указания клиенту выполнять какие либо действия при возникновении ошибки,
            или null
            'payload_data': Содержит полезные данные для ошибок,
            например оставшиеся количество секунд для отправки кода п
            одтверждения, или ошибки со сторонних сервисов.
            Зависит от поля code, или status_code == 502
        }
    """

    def __init__(self, detail=None, validation_errors=None, code=None, payload_data=None):
        self.detail = {
            'status': self.status_code,
            'detail': detail,
            'validation_errors': validation_errors,
            'code': code,
            'payload_data': payload_data
        }


class Validate(BaseErrorResponse):
    status_code = status.HTTP_400_BAD_REQUEST


class Conflict(BaseErrorResponse):
    status_code = status.HTTP_409_CONFLICT


def custom_exception_handler(exc, context):
    """Custom error handler"""

    if isinstance(exc, BaseErrorResponse):
        return exception_handler(exc, context)
    else:

        if isinstance(exc, Http404):
            exc = exceptions.NotFound()
        elif isinstance(exc, PermissionDenied):
            exc = exceptions.PermissionDenied()

        if isinstance(exc, exceptions.APIException):
            headers = {}
            if getattr(exc, 'auth_header', None):
                headers['WWW-Authenticate'] = exc.auth_header
            if getattr(exc, 'wait', None):
                headers['Retry-After'] = '%d' % exc.wait

            data = dict()

            data['status'] = exc.status_code
            data['code'] = exc.__class__.__name__
            data['detail'] = None
            data['payload_data'] = None
            data['validation_errors'] = None

            if exc.status_code == 400:
                data['validation_errors'] = exc.detail
            else:
                if isinstance(exc.detail, str):
                    data['detail'] = exc.detail
                else:
                    data['payload_data'] = exc.detail

            set_rollback()
            return Response(data, status=exc.status_code, headers=headers)

        return None
