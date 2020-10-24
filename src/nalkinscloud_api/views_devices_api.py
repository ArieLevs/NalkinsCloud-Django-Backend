import logging

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from nalkinscloud_mosquitto.functions import is_device_id_exists, \
    is_device_owned_by_user, \
    update_device_pass, remove_from_customer_devices, remove_from_access_list
from nalkinscloud_mosquitto.models import CustomerDevice
from nalkinscloud_api.functions import build_json_response, generate_random_8_char_string, hash_pbkdf2_sha256_password

# Import serializers
from nalkinscloud_api.serializers_devices import CustomerDeviceCreateSerializer, DeviceSerializer, \
    CustomerDeviceSerializer

# REST Framework
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
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


class GetDevicePassView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        serializer = DeviceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New GetDevicePass request")

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            device_id = data['device_id']

            if not is_device_id_exists(device_id):
                message = 'failed'
                value = 'Device does not exists'
                logger.info("Device " + device_id + "does not exists")
                response_code = status.HTTP_204_NO_CONTENT
            else:
                # Get token from request
                token = request.auth
                email = token.user
                user = User.objects.get(email=email)

                logger.info("Current logged in user: " + str(email) + " ID is: " + str(user))

                # Check if the activated device is new (never got activated)
                # or the original user is activating his device again
                if not is_device_owned_by_user(device_id, user):
                    message = 'failed'
                    value = 'User is not the owner'
                    logger.info("User is not the owner")
                    response_code = status.HTTP_409_CONFLICT
                else:
                    logger.info("All checks passed, generating hashed pass")
                    # Generate the password (8 characters long mixed digits with letters)
                    # The 'newPassword' should be returned to the app
                    new_password = generate_random_8_char_string()

                    # update the pass into the DB,
                    # send device ID, pass and the device name that the user choose
                    # NOTE - password is being hashed on device.save def
                    if update_device_pass(device_id, new_password):
                        message = 'success'
                        value = new_password
                        logger.info("Password updated")
                        response_code = status.HTTP_200_OK
                    else:
                        message = 'failed'
                        value = 'Password Update Failed'
                        logger.info("Password Update Failed")
                        response_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            return Response(build_json_response(message, value), status=response_code)
