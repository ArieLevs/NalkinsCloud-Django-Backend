import logging
from ipware.ip import get_client_ip
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from nalkinscloud_api.scheduler import schedule_new_job, remove_job_by_id
from nalkinscloud_mosquitto.functions import insert_into_access_list, is_device_id_exists, \
    is_device_owned_by_user, \
    update_device_pass, remove_from_customer_devices, remove_from_access_list
from nalkinscloud_mosquitto.models import Device, CustomerDevice
from nalkinscloud_api.functions import build_json_response, is_client_secret_exists, is_email_exists, \
    generate_random_8_char_string, hash_pbkdf2_sha256_password, get_utc_datetime

# Import serializers
from nalkinscloud_api.serializers import RegistrationSerializer, DeviceActivationSerializer, ForgotPasswordSerializer, \
    DeviceIdOnlySerializer, ResetPasswordSerializer, SetScheduledJobSerializer, CustomerDeviceSerializer

# REST Framework
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.exceptions import NotFound

from django.contrib.auth.forms import PasswordResetForm

User = get_user_model()

# Define logger
logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        logger.info("HealthCheckView request")

        # Get token from request
        token = request.auth
        email = str(token.user)
        logger.info("request from user: " + email)

        message = 'success'

        # If all passed OK return user name
        logger.info("Success, health_check passed OK")
        return Response(build_json_response(message, email), status=status.HTTP_200_OK)


class RegistrationView(CreateAPIView):
    permission_classes = ()  # No Authentication needed here
    serializer_class = RegistrationSerializer
    queryset = User.objects.all()


class DeviceActivationView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeviceActivationSerializer
    model = Device

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device_id = None
        self.device_name = None

    def get_queryset(self):
        return get_object_or_404(self.model, device_id=self.device_id)

    def put(self, request, *args, **kwargs):
        serializer = DeviceActivationSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.device_id = serializer.data['device_id']
        self.device_name = serializer.data['device_name']

        # get the device that's being activated
        device = self.get_queryset()

        # get users device (type user, model application)
        try:
            user_device = Device.objects.get(device_id=self.request.user)
        except ObjectDoesNotExist:
            logger.error('mqtt device for {} was not found, '
                         'it should of been generated on registration,'
                         ' but missing from db at this point.'.format(self.request.user))
            return Response('device activation failed', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # create or update current device, with user in request
        new_customer_device, created = CustomerDevice.objects.update_or_create(
            user_id=self.request.user, device_id=device,
            defaults={'device_name': self.device_name, 'is_owner': True}
        )

        logger.info("customer device {} completed, created: {}".format(
            new_customer_device, created
        ))

        # Build the topic, combined with userId + deviceId
        topic = self.device_id + "/#"
        # Insert the device into 'access_list' table
        insert_into_access_list(device, topic)
        insert_into_access_list(user_device, topic)
        logger.info("insert_into_access_list_mosquitto_db completed")

        return Response('activation successfully completed', status=status.HTTP_200_OK)


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


class ForgotPasswordView(APIView):
    permission_classes = ()

    @staticmethod
    def post(request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New ForgotPassword request")

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            client_secret = data['client_secret']

            client_ip, is_routable = get_client_ip(request)
            if client_ip is None:
                client_ip = '0.0.0.0'

            # Get CLIENT_SECRET from DB ( if user is using a verified software )
            if not is_client_secret_exists(client_secret):
                message = 'failed'
                value = 'Application could not be verified'
                response_code = status.HTTP_401_UNAUTHORIZED
            else:
                if not is_email_exists(data['email']):  # Check if email exists
                    # Notify user all went OK, even if email does not exists
                    # this is done to prevent email exposes
                    message = 'success'
                    value = 'Forgot Password Process completed'
                    response_code = status.HTTP_200_OK
                    logger.error("Error, email does not exist")
                else:
                    # If all passed OK
                    form = PasswordResetForm(data)
                    if not form.is_valid():
                        message = 'failed'
                        value = 'Form is not valid'
                        logger.info("Forgot password form is NOT valid")
                        response_code = status.HTTP_400_BAD_REQUEST
                    else:
                        logger.info("Forgot password form is valid")
                        form.save(request=request)
                        logger.info("Success, Email sent to: " + data['email'])
                        message = 'success'
                        value = 'Forgot Password Process completed'
                        response_code = status.HTTP_200_OK

            return Response(build_json_response(message, value), status=response_code)


class GetDevicePassView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        serializer = DeviceIdOnlySerializer(data=request.data)

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


class GetScheduledJobView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        # Print request to log file
        logger.info("New GetScheduledJob request")

        token = request.auth
        email = token.user
        user_id = token.user_id

        # TODO Write 'get scheduled jobs logic
        # If all passed OK return job id (value)
        logger.info("Success, scheduled job passed OK")
        message = 'success'

        json_array = []
        # Append current details (device) to the array
        json_array.append({"device_id": "device_id", "device_name": "just some name", "job_id": "some id"})
        # value = json_array  # Set the final json array to 'value'
        value = 'Scheduled jobs have not developed yet'

        return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class RemoveDeviceView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        serializer = DeviceIdOnlySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New RemoveDevice request")

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            device_id_string = data['device_id']

            # Get token from request
            token = request.auth
            email = token.user
            user = User.objects.get(email=email)
            device = Device.objects.get(device_id=device_id_string)

            logger.info("Current logged in user: " + str(email) + " ID is: " + str(user))

            if not is_device_owned_by_user(device, user):
                message = 'failed'
                value = 'You cannot remove this device'
                logger.error("User is not the device owner")
                response_code = status.HTTP_409_CONFLICT
            else:
                remove_from_customer_devices(user, device)

                remove_from_access_list(email, device_id_string + '%')
                remove_from_access_list(device.device_id, device_id_string + '%')

                # Update device pass with some random pass
                new_password = generate_random_8_char_string()

                # Do hash on the new password
                hashed_pass = hash_pbkdf2_sha256_password(new_password)

                # update the hashed pass into the DB,
                # send device ID, hashed pass and the device name that the user choose
                update_device_pass(device, hashed_pass)

                message = "success"
                value = "Device Removed from account"
                response_code = status.HTTP_200_OK

            return Response(build_json_response(message, value), status=response_code)


class ResetPasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New ResetPassword request")

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            current_password = data['current_password']
            new_password = data['new_password']

            # Get token from request
            token = request.auth
            email = token.user
            user_object = User.objects.get(email=email)
            logger.info("Current logged in user name: " + str(email) + " ID is: " + str(user_object))

            if not user_object.check_password(current_password):
                message = 'failed'
                value = 'Current Password is incorrect'
                logger.info("Current Password is incorrect")
                response_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            else:
                user_object.set_password(new_password)
                user_object.save()
                message = 'success'
                value = 'Password have been changed'
                logger.info("New password successfully set")
                response_code = status.HTTP_200_OK

            return Response(build_json_response(message, value), status=response_code)


class SetScheduledJobView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        logger.info("New SetScheduledJob request")

        serializer = SetScheduledJobSerializer(data=request.data)

        if not serializer.is_valid():
            logger.info(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            device_id = data['app_params']['device_id']

            # Get token from request
            token = request.auth
            email = token.user
            user_id = token.user_id

            logger.info("Current logged in user name: " + str(email) + " ID is: " + str(user_id))

            if not is_device_owned_by_user(device_id, user_id):
                message = 'failed'
                value = 'You cannot set new job for this device'
                logger.error("User %s is not owner of device %s" % (user_id, device_id))
            else:
                from datetime import datetime

                # This 'local_start_date' time, in this format:
                # datetime.datetime(2017, 5, 24, 11, 45, tzinfo=datetime.timezone(datetime.timedelta(0, 10800)))
                # the tzinfo represents a local GMT time
                # get start datetime object (local time) from json
                local_start_date = datetime.strptime(data["start_date_time"]["start_date_time_values"],
                                                     '%Y-%m-%d %H:%M:%S%z')

                # This 'utc_date' time, in this format:
                # datetime.datetime(2017, 5, 31, 10, 4, tzinfo=<UTC>), In UTC time
                # Sent 'local_start_date' to the 'get_utc_datetime' function
                utc_start_date = get_utc_datetime(local_start_date)

                # get boolean object from json, representing a repeated job or not
                is_repeated_job = data['repeated_job']['repeat_job']  # Boolean var

                # For each filed in relevant json section
                days_to_repeat = data['repeated_job']['repeat_days']  # Dictionary var

                # Get what will be done from json object
                # True = 1 (turn on)
                # False = 0 (turn off)
                job_action = data['job_action']  # Boolean var

                # get boolean object from json, representing if end date selected
                end_date_time_selected = data['end_date_time']['end_date_time_selected']  # Boolean var
                # This 'local_end_date' time, in this format:
                # datetime.datetime(2017, 5, 24, 11, 45, tzinfo=datetime.timezone(datetime.timedelta(0, 10800)))
                # the tzinfo represents a local GMT time
                # get start datetime object (local time) from json
                local_end_date = datetime.strptime(data["end_date_time"]["end_date_time_values"],
                                                   '%Y-%m-%d %H:%M:%S%z')

                # This 'utc_date' time, in this format:
                # datetime.datetime(2017, 5, 31, 10, 4, tzinfo=<UTC>), In UTC time
                # Sent 'local_start_date' to the 'get_utc_datetime' function
                utc_end_date = get_utc_datetime(local_end_date)

                # Get the topic from json object, this topic will be used to send a message to
                topic_to_execute = data['app_params']['topic']

                # TODO Send job to Celery

                # Execute the job, and get its job id into value
                value = schedule_new_job(device_id, topic_to_execute, is_repeated_job,
                                         days_to_repeat, job_action,
                                         end_date_time_selected, utc_start_date, utc_end_date)

                # If all passed OK return job id (value)
                logger.info("Success, scheduled job passed OK")
                message = 'success'

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class DelScheduledJobView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        serializer = DeviceIdOnlySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New DelScheduledJob request")

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            # Get token from request
            token = request.auth
            email = token.user
            user_id = token.user_id

            logger.info("Current logged in user name: " + str(email) + " ID is: " + str(user_id))

            # Get the job id that needs to be removed
            job_id = data['job_id']
            logger.info("job_id: " + job_id)

            # Start remove function from 'scheduler'
            remove_job_by_id(job_id)

            # If all passed OK return job id (value)
            logger.info("Success, scheduled job passed OK")
            message = 'success'
            value = 'job' + job_id + 'removed'

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class UpdateMQTTUserPassView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    model = Device

    def get_queryset(self):
        return get_object_or_404(self.model, device_id=self.request.user)

    def put(self, request, *args, **kwargs):
        device = self.get_queryset()
        device.set_password(request.auth.token)
        device.save()
        return Response('device pass update was successful', status=status.HTTP_200_OK)


class SetScheduledJobView2(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        logger.info("SetScheduledJob Request Parameters: " + str(request.data))
        return Response("SDF", status=status.HTTP_200_OK)


class ReadinessProbe(APIView):
    permission_classes = ()  # No Authentication needed here

    @staticmethod
    def post(request):
        return Response('ok', status=status.HTTP_200_OK)

    @staticmethod
    def get(request):
        return Response('ok', status=status.HTTP_200_OK)


class LivenessProbe(APIView):
    permission_classes = ()  # No Authentication needed here

    @staticmethod
    def post(request):
        logger.debug("liveness_probe request")
        return Response('ok', status=status.HTTP_200_OK)

    @staticmethod
    def get(request):
        logger.debug("liveness_probe request")
        return Response('ok', status=status.HTTP_200_OK)
