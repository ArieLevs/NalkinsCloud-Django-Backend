import logging

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from nalkinscloud_mosquitto.functions import update_device_pass, remove_from_customer_devices, remove_from_access_list
from nalkinscloud_mosquitto.models import CustomerDevice, Device
from nalkinscloud_api.functions import generate_random_8_char_string, hash_pbkdf2_sha256_password

# Import serializers
from nalkinscloud_api.serializers_devices import CustomerDeviceCreateSerializer, CustomerDeviceSerializer

# REST Framework
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView, UpdateAPIView
from rest_framework.exceptions import NotFound

User = get_user_model()

# Define logger
logger = logging.getLogger(__name__)


class CustomerDevicesView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerDeviceSerializer
    model = CustomerDevice

    def get_queryset(self):
        return get_object_or_404(self.model, user_id=self.request.user, device_id=self.kwargs['c_device_id'])

    def retrieve(self, request, *args, **kwargs):
        customer_device = self.get_queryset()
        serializer = CustomerDeviceSerializer(customer_device)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        customer_device = self.get_queryset()
        serializer = CustomerDeviceSerializer(customer_device)

        if not customer_device.is_owner:
            logger.error('user {} is not the owner of {}'.format(customer_device.user_id, customer_device.device_id))
            return Response('You cannot remove this device', status=status.HTTP_409_CONFLICT)
        else:
            remove_from_customer_devices(customer_device.user_id, customer_device.device_id)

            remove_from_access_list(customer_device.user_id, str(customer_device.device_id) + '%')
            remove_from_access_list(customer_device.device_id, str(customer_device.device_id) + '%')

            # Update device pass with some random pass
            new_password = generate_random_8_char_string()

            # Do hash on the new password
            hashed_pass = hash_pbkdf2_sha256_password(new_password)

            # update the hashed pass into the DB,
            # send device ID, hashed pass and the device name that the user choose
            update_device_pass(customer_device.user_id, hashed_pass)

            logger.error('user {} removed device {}'.format(customer_device.user_id, customer_device.device_id))

        return Response(serializer.data)


class CustomerDeviceCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerDeviceCreateSerializer
    # queryset = CustomerDevice.objects.all()


class DeviceListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerDeviceSerializer
    model = CustomerDevice

    def get_queryset(self):
        result = self.model.objects.filter(user_id=self.request.user)
        if result:
            return result
        else:
            raise NotFound()


class DevicePassUpdateView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Device.objects.all()
    lookup_field = 'device_id'

    def update(self, request, *args, **kwargs):
        device = self.get_object()

        if device.type.type == 'user':
            # make sure user is updating his own devices password
            if device.device_id != self.request.user.email:
                logger.error("User {} is trying to update another users device password {}".format(
                    self.request.user, device)
                )
                return Response('device pass update failed', status=status.HTTP_409_CONFLICT)
            device.set_password(request.auth.token)
            device.save()
            return Response('device pass update was successful', status=status.HTTP_200_OK)
        else:
            customer_device = CustomerDevice.objects.get(user_id=self.request.user, device_id=device)
            if not customer_device.is_owner:
                logger.error("User {} is not the owner of device {}".format(self.request.user, device))
                return Response('device pass update failed', status=status.HTTP_409_CONFLICT)

            # Generate the password (8 characters long mixed digits with letters)
            new_password = generate_random_8_char_string()
            device.set_password(new_password)
            device.save()
            return Response({'password': new_password}, status=status.HTTP_200_OK)
