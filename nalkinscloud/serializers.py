
# REST API
from rest_framework import serializers


# Setup view serializers

class RegistrationSerializer(serializers.Serializer):
    client_secret = serializers.CharField(required=True, max_length=256)
    username = serializers.CharField(required=True, max_length=100)
    email = serializers.CharField(required=True, max_length=256)
    password = serializers.CharField(required=True, max_length=100)
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)


class DeviceActivationSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True, max_length=256)
    device_name = serializers.CharField(required=True, max_length=256)


class ForgotPasswordSerializer(serializers.Serializer):
    client_secret = serializers.CharField(required=True, max_length=256)
    email = serializers.CharField(required=True, max_length=256)


class DeviceIdOnlySerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True, max_length=256)


class ResetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, max_length=256)
    new_password = serializers.CharField(required=True, max_length=256)


class SetScheduledJobSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True, max_length=256)
    # TODO Check serializer for this API, as it contains more complex JSON Array


class DelScheduledJobSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True, max_length=256)
    job_id = serializers.CharField(required=True, max_length=256)
