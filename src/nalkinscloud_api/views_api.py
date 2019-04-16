import logging
from ipware.ip import get_real_ip

from nalkinscloud_django.settings import PROJECT_NAME, FRONTEND_DOMAIN, EMAIL_HOST_USER
from nalkinscloud_api.scheduler import schedule_new_job, remove_job_by_id
from nalkinscloud_mosquitto.functions import *
from nalkinscloud_api.functions import *
from django_user_email_extension.models import *

# Import serializers
from nalkinscloud_api.serializers import *

# REST Framework
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse

# Define logger
logger = logging.getLogger(PROJECT_NAME)


class HealthCheckView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logger.info("HealthCheckView request at: " + str(datetime.datetime.now()))

        # Get token from request
        token = request.auth
        email = str(token.user)
        logger.info("request from user: " + email)

        message = 'success'

        # If all passed OK return user name
        logger.info("Success, health_check passed OK")
        return Response(build_json_response(message, email), status=status.HTTP_200_OK)


class RegistrationView(APIView):
    permission_classes = ()  # No Authentication needed here

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        # Check format and unique constraint
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        logger.info("New Registration request at: " + str(datetime.datetime.now()))

        data = serializer.data
        logger.info("Request Parameters: " + str(data))

        ip = get_real_ip(request)
        if ip is not None:
            logger.error('Could not detect IP of request')
            ip = '0.0.0.0'

        # Get CLIENT_SECRET from DB ( if user is using a verified software
        if not is_client_secret_exists(data['client_secret']):
            message = 'failed'
            value = 'Application could not be verified'
            response_code = status.HTTP_401_UNAUTHORIZED
        else:
            if is_email_exists(data['email']):  # Check if email already exists
                message = 'failed'
                value = 'Email already exists'
                response_code = status.HTTP_409_CONFLICT
                logger.error('%s - Email already exists', data['email'])
            else:

                # Create new django user
                new_user = User.objects.create_user(data['email'],
                                                    data['password'])

                new_user.first_name = data['first_name']
                new_user.last_name = data['last_name']
                new_user.user_name = generate_user_name(data['first_name'], data['last_name'])

                logger.info("Setting up MQTT broker db info")
                # Add new "device" (customer) to the devices table
                if not insert_new_client_to_devices(data['email'], data['password'], ip):
                    message = 'failed'
                    value = 'Registration Error occur'
                    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    logger.error('Failed to add %s record to devices table', data['email'])
                else:
                    # Insert the customer into 'acls' table, with topic of: email/#
                    insert_into_acls_mosquitto_db(data['email'], data['email'] + "/#")

                    new_user.registration_ip = ip
                    new_user.is_active = False
                    new_user.save()

                    logger.info("Setting up verification process")
                    new_user.create_verification_email()

                    subject = 'Verify your NalkinsCloud account'
                    body = 'Follow this link to verify your account: ' + \
                           FRONTEND_DOMAIN + '%s' % reverse('verify_account',
                                                            kwargs={'uuid': str(new_user.get_uuid_of_email())})

                    new_user.send_verification_email(subject=subject,
                                                     body=body,
                                                     from_mail=EMAIL_HOST_USER)
                    message = 'success'
                    value = 'Registered!'
                    response_code = status.HTTP_201_CREATED
                    logger.info("success Registered!")
        return Response(build_json_response(message, value), status=response_code)


class DeviceActivationView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DeviceActivationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New DeviceActivation request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            device_id = data['device_id']
            device_name = data['device_name']

            if not is_device_id_exists(device_id):
                message = 'failed'
                value = 'Device does not exists'
                response_code = status.HTTP_204_NO_CONTENT
                logger.error("Device does not exists")
            else:
                # Get token from request
                token = request.auth
                email = token.user
                user_id = token.user_id

                logger.info("Current logged in user: " + str(email) + " ID is: " + str(user_id))

                # Check if the activated device is new (never got activated)
                # or the original username is activating his device again
                if not get_device_owner(device_id, user_id):
                    message = 'failed'
                    value = 'Device already associated'
                    response_code = status.HTTP_409_CONFLICT
                    logger.error("Device already associated")
                else:
                    logger.info("All checks passed, activating device")

                    # Insert the device into 'customer_devices' table
                    if not insert_into_customer_devices(user_id, device_id, device_name):
                        message = 'failed'
                        value = 'Device Activation Failed'
                        response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                        logger.error('Failed to add new device to customers_devices table')
                    else:
                        logger.info("insert_into_customer_devices completed")

                        # Build the topic, combined with userId + deviceId
                        topic = device_id + "/#"
                        # Insert the device into 'acls' table
                        insert_into_acls_mosquitto_db(device_id, topic)
                        insert_into_acls_mosquitto_db(email, topic)
                        logger.info("insert_into_acls_mosquitto_db completed")

                        message = 'success'
                        value = 'Activation successfully completed'
                        response_code = status.HTTP_200_OK
            return Response(build_json_response(message, value), status=response_code)


class DeviceListView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # Print request to log file
        logger.info("New DeviceList request at: " + str(datetime.datetime.now()))

        token = request.auth
        email = token.user
        user_id = token.user_id
        logger.info("request from user: " + str(email))

        device_list = get_customers_devices(user_id)  # Get list of devices from the DB
        if not device_list:
            message = 'failed'
            value = 'no devices found'
            response_code = status.HTTP_204_NO_CONTENT
            logger.info('No devices found')
        else:
            logger.info("User: " + str(email) + " Devices found: " + str(device_list))

            json_array = []
            # Build Json array from the 'device_list' response from the DB
            for device in device_list:
                device_id = str(device.device_id)
                device_name = str(device.device_name)
                device_type = str(device.device_id.type)

                tmp_json = {"device_id": device_id, "device_name": device_name, "device_type": device_type}

                json_array.append(tmp_json)  # Append current details (device) to the array
                logger.info(json_array)
            response_code = status.HTTP_200_OK
            message = 'success'
            value = json_array  # Set the final json array to 'value'

        return Response(build_json_response(message, value), status=response_code)


class ForgotPasswordView(APIView):
    permission_classes = ()

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New ForgotPassword request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            client_secret = data['client_secret']

            ip = get_real_ip(request)
            if ip is not None:
                logger.error('Could not detect IP of request')
                ip = 'none'

            # Get CLIENT_SECRET from DB ( if user is using a verified software )
            if not is_client_secret_exists(client_secret):
                message = 'failed'
                value = 'Application could not be verified'
            else:
                if not is_email_exists(data['email']):  # Check if email exists
                    logger.error("Error, email does not exist")
                    # Notify user all went OK
                    message = 'success'
                    value = 'Forgot Password Process completed'
                else:
                    # If all passed OK
                    form = PasswordResetForm(data)
                    if not form.is_valid():
                        message = 'failed'
                        value = 'Form is not valid'
                        logger.info("Forgot password form is NOT valid")
                    else:
                        logger.info("Forgot password form is valid")
                        form.save(request=request)
                        logger.info("Success, Email sent to: " + data['email'])
                        message = 'success'
                        value = 'Forgot Password Process completed'

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class GetDevicePassView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DeviceIdOnlySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New GetDevicePass request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            device_id = data['device_id']

            if not is_device_id_exists(device_id):
                message = 'failed'
                value = 'Device does not exists'
                logger.info("Device " + device_id + "does not exists")
            else:
                # Get token from request
                token = request.auth
                email = token.user
                user_id = token.user_id

                logger.info("Current logged in user: " + str(email) + " ID is: " + str(user_id))

                # Check if the activated device is new (never got activated)
                # or the original user is activating his device again
                if not get_device_owner(device_id, user_id):
                    message = 'failed'
                    value = 'Device already associated'
                    logger.info("Device already associated")
                else:
                    logger.info("All checks passed, generating hashed pass")
                    # Generate the password (8 characters long mixed digits with letters)
                    # The 'newPassword' should be returned to the app
                    new_password = generate_random_8_char_string()
                    # logger.info("New password generated: " + new_password)

                    # update the pass into the DB,
                    # send device ID, pass and the device name that the user choose
                    # NOTE - password is being hashed on device.save def
                    if update_device_pass_mosquitto_db(device_id, new_password):
                        logger.info("Password updated")

                        # Set success values
                        message = 'success'
                        value = new_password
                    else:
                        logger.info("Password Update Failed")

                        # Set success values
                        message = 'failed'
                        value = 'Password Update Failed'

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class GetScheduledJobView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # Print request to log file
        logger.info("New GetScheduledJob request at: " + str(datetime.datetime.now()))

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
        value = json_array  # Set the final json array to 'value'
        value = 'Scheduled jobs have not developed yet'

        return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class RemoveDeviceView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DeviceIdOnlySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New RemoveDevice request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            device_id = data['device_id']

            # Get token from request
            token = request.auth
            email = token.user
            user_id = token.user_id

            logger.info("Current logged in user: " + str(email) + " ID is: " + str(user_id))

            if not get_device_owner(device_id, user_id):
                message = 'failed'
                value = 'You cannot remove this device'
                logger.error("User is not the device owner")
            else:
                remove_from_customer_devices(user_id, device_id)

                remove_from_acls(email, device_id + '%')
                remove_from_acls(device_id, device_id + '%')

                # Update device pass with some random pass
                new_password = generate_random_8_char_string()

                # Do hash on the new password
                hashed_pass = hash_pbkdf2_sha256_password(new_password)

                # update the hashed pass into the DB,
                # send device ID, hashed pass and the device name that the user choose
                update_device_pass_mosquitto_db(device_id, hashed_pass)

                logger.info("Password updated")

                message = "success"
                value = "Device Removed from account"

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New ResetPassword request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            current_password = data['current_password']
            new_password = data['new_password']

            # Get token from request
            token = request.auth
            email = token.user
            user_id = token.user_id

            logger.info("Current logged in user name: " + str(email) + " ID is: " + str(user_id))

            user_object = User.objects.get(id=user_id)

            if not user_object.check_password(current_password):
                message = 'failed'
                value = 'Current Password is incorrect'
                logger.info("Current Password is incorrect")
            else:
                user_object.set_password(new_password)
                user_object.save()
                message = 'success'
                value = 'Password have been changed'
                logger.info("New password successfully set")

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class SetScheduledJobView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logger.info("New SetScheduledJob request at: " + str(datetime.datetime.now()))

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

            if not get_device_owner(device_id, user_id):
                message = 'failed'
                value = 'You cannot set new job for this device'
                logger.error("User %s is not owner of device %s" % (user_id, device_id))
            else:
                # This 'local_start_date' time, in this format:
                # datetime.datetime(2017, 5, 24, 11, 45, tzinfo=datetime.timezone(datetime.timedelta(0, 10800)))
                # the tzinfo represents a local GMT time
                # get start datetime object (local time) from json
                local_start_date = datetime.datetime.strptime(data["start_date_time"]["start_date_time_values"],
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
                local_end_date = datetime.datetime.strptime(data["end_date_time"]["end_date_time_values"],
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

    def post(self, request):
        serializer = DeviceIdOnlySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.info("New DelScheduledJob request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logger.info("Request Parameters: " + str(data))

            device_id = data['device_id']

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


class UpdateMQTTUserPassView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logger.info("New UpdateMQTTUserPass request at: " + str(datetime.datetime.now()))

        # Get token from request
        token = request.auth
        email = token.user
        user_id = token.user_id

        logger.info("Current logged in user: " + str(email) + " ID is: " + str(user_id))

        # If all passed OK, update customer "device" pass
        if update_device_pass_mosquitto_db(email, token):
            # Return user name
            message = 'success'
            value = str(email)
        else:
            message = 'failed'
            value = 'update device pass failed'

        return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class SetScheduledJobView2(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logger.info("New SetScheduledJob request at: " + str(datetime.datetime.now()))

        logger.info("Request Parameters: " + str(request.data))

        return Response("SDF", status=status.HTTP_200_OK)
