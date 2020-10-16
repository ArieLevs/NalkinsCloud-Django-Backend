
from rest_framework.exceptions import APIException
from rest_framework import status

from django.utils.encoding import force_text


class CustomException(APIException):
    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'

    def __init__(self, detail, field, status_code=None):
        if status_code is not None:
            self.status_code = self.default_status_code
        if detail is not None:
            self.detail = {field: force_text(detail)}
        else:
            self.detail = {'detail': force_text(self.default_detail)}
