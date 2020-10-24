import logging
from ipware.ip import get_client_ip

# REST API
from rest_framework import serializers

from django.contrib.auth import get_user_model  # If used custom user model
from django.conf import settings
from django.urls import reverse

from nalkinscloud_mosquitto.models import Device
from nalkinscloud_api.functions import generate_user_name
from nalkinscloud_api.api_exceptions import CustomException
from nalkinscloud_mosquitto.functions import insert_into_access_list, insert_new_client_to_devices

User = get_user_model()
logger = logging.getLogger(__name__)


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name',)
        write_only_fields = ('password',)

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'], password=validated_data['password'],
            first_name=validated_data['first_name'], last_name=validated_data['last_name'],
            user_name=generate_user_name(validated_data['first_name'], validated_data['last_name']),
        )

        client_ip, is_routable = get_client_ip(self.context['request'])
        if client_ip is None:
            client_ip = '0.0.0.0'
        logger.info('new registration attempt from {}'.format(client_ip))

        logger.info('setting up MQTT broker db info')
        # Add new "device" (customer) to the devices table
        if not insert_new_client_to_devices(validated_data['email'], validated_data['password'], client_ip):
            logger.error('failed to add {} record to devices table'.format(validated_data['email']))
            # default exception is error 500
            raise CustomException(detail=None, field=None)
        else:
            # Insert the customer into 'access_list' table, with topic of: email/#
            device = Device.objects.get(device_id=validated_data['email'])
            insert_into_access_list(device, validated_data['email'] + "/#")

            logger.info("Setting up verification process")
            user.save()

            user.create_verification_email()

            subject = 'Verify your NalkinsCloud account'
            body = 'Follow this link to verify your account: ' + settings.FRONTEND_DOMAIN + '{}'.format(
                reverse('nalkinscloud_ui:verify_account', kwargs={'verification_uuid': str(user.get_uuid_of_email())})
            )

            user.send_verification_email(subject=subject,
                                         body=body,
                                         from_mail=settings.EMAIL_HOST_USER)

            logger.info('user {} successfully registered'.format(user))

        return user


class ForgotPasswordSerializer(serializers.Serializer):
    client_secret = serializers.CharField(required=True, max_length=256)
    email = serializers.CharField(required=True, max_length=256)

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
