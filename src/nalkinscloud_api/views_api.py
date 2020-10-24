import logging
from ipware.ip import get_client_ip
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from nalkinscloud_api.scheduler import schedule_new_job, remove_job_by_id
from nalkinscloud_mosquitto.functions import is_device_owned_by_user
from nalkinscloud_mosquitto.models import Device
from nalkinscloud_api.functions import build_json_response, is_client_secret_exists, is_email_exists, get_utc_datetime

# Import serializers
from nalkinscloud_api.serializers import RegistrationSerializer, ForgotPasswordSerializer, \
    ResetPasswordSerializer, SetScheduledJobSerializer
from nalkinscloud_api.serializers_devices import DeviceSerializer

# REST Framework
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView, CreateAPIView

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
        serializer = DeviceSerializer(data=request.data)

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
