
from rest_framework.exceptions import APIException
from rest_framework import status

from django.utils.encoding import force_text


class CustomException(APIException):
    def __init__(self, detail, field, status_code=None):
        if status_code is not None:
            self.status_code = status_code

        if detail is not None:
            self.detail = {field: force_text(detail)}
        else:
            self.detail = {'detail': force_text(self.default_detail)}
