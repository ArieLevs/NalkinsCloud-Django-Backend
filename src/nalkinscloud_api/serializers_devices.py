import logging

# REST API
from rest_framework import serializers

from django.core.exceptions import ObjectDoesNotExist

from nalkinscloud_mosquitto.models import Device, CustomerDevice
from nalkinscloud_api.api_exceptions import CustomException
from nalkinscloud_mosquitto.functions import insert_into_access_list


logger = logging.getLogger(__name__)


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('device_id', 'model', 'type',)
        depth = 1


class CustomerDeviceSerializer(serializers.ModelSerializer):
    # get a device using DeviceSerializer, later add it to this serialized
    device = DeviceSerializer(source="device_id", many=False)

    class Meta:
        model = CustomerDevice
        fields = ('user_id', 'device')


class CustomerDeviceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDevice
        fields = ('device_id', 'device_name')

    def create(self, validated_data):

        # get the device that's being activated
        device = Device.objects.get(device_id=validated_data['device_id'])

        # get users device (type user, model application)
        try:
            user_device = Device.objects.get(device_id=self.context['request'].user)
        except ObjectDoesNotExist:
            logger.error('mqtt device for {} was not found, '
                         'it should of been generated on registration,'
                         ' but missing from db at this point.'.format(self.context['request'].user))
            raise CustomException(detail='device activation failed', field=None)

        # create or update current device, with user in request
        new_customer_device, created = CustomerDevice.objects.update_or_create(
            user_id=self.context['request'].user, device_id=device,
            defaults={'device_name': validated_data['device_name'], 'is_owner': True}
        )

        logger.info("customer device {} completed, created: {}".format(
            new_customer_device, created
        ))

        # Build the topic, combined with userId + deviceId
        topic = str(validated_data['device_id']) + "/#"
        # Insert the device into 'access_list' table
        insert_into_access_list(device, topic)
        insert_into_access_list(user_device, topic)
        logger.info("insert_into_access_list_mosquitto_db completed")

        return new_customer_device
