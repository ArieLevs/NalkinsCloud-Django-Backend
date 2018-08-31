
# REST API
from rest_framework import serializers


class RegistrationSerializer(serializers.Serializer):
    client_secret = serializers.CharField(required=True, max_length=256)
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


class StartDateTimeSerializer(serializers.Serializer):
    start_date_time_selected = serializers.BooleanField(required=True)
    start_date_time_values = serializers.CharField(required=True, max_length=256)


class EndDateTimeSerializer(serializers.Serializer):
    end_date_time_selected = serializers.BooleanField(required=True)
    end_date_time_values = serializers.CharField(required=True, max_length=256)


class RepeatedDaysSerializer(serializers.Serializer):
    sunday = serializers.BooleanField(required=True)
    monday = serializers.BooleanField(required=True)
    tuesday = serializers.BooleanField(required=True)
    wednesday = serializers.BooleanField(required=True)
    thursday = serializers.BooleanField(required=True)
    friday = serializers.BooleanField(required=True)
    saturday = serializers.BooleanField(required=True)



class RepeatedJobSerializer(serializers.Serializer):
    repeat_job = serializers.BooleanField(required=True)
    repeat_days = RepeatedDaysSerializer(source='*')


class AppParamsSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True, max_length=256)
    topic = serializers.CharField(required=True, max_length=256)


class SetScheduledJobSerializer(serializers.Serializer):
    app_params = AppParamsSerializer(required=True, source='*')
    repeated_job = RepeatedJobSerializer(required=True, source='*')
    job_action = serializers.BooleanField(required=True)
    start_date_time = StartDateTimeSerializer(required=True, source='*')
    end_date_time = EndDateTimeSerializer(required=True, source='*')


class DelScheduledJobSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True, max_length=256)
    job_id = serializers.CharField(required=True, max_length=256)
