import logging

from nalkinscloud.scheduler import schedule_new_job, remove_job_by_id
from nalkinscloud.db_functions import *
from nalkinscloud.functions import *
from django.conf import settings
from ipware.ip import get_real_ip
from django.http import Http404
from django.shortcuts import render, redirect

from nalkinscloud.models import EmailVerification

# REST Framework
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.contrib.auth.models import *
from django.contrib.auth.forms import PasswordResetForm

# Import serializers
from nalkinscloud.serializers import *


class HealthCheckView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
        logging.info("New HealthCheck request at: " + str(datetime.datetime.now()))

        logging.info("Request Parameters: " + str(request))

        # Get token from request
        token = request.auth
        user_name = str(token.user)

        message = 'success'

        # If all passed OK return user name
        logging.info("Success, health_check passed OK")
        return Response(build_json_response(message, user_name), status=status.HTTP_200_OK)


class RegistrationView(APIView):
    """ Allow registration of new users. """
    permission_classes = ()  # No Authentication needed here

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        # Check format and unique constraint
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
        logging.info("New Registration request at: " + str(datetime.datetime.now()))

        data = serializer.data
        logging.info("Request Parameters: " + str(data))

        ip = get_real_ip(request)
        if ip is not None:
            logging.error('Could not detect IP of request')
            ip = 'none'

        # Get CLIENT_SECRET from DB ( if user is using a verified software
        if not get_client_secret_web_db(data['client_secret']):
            message = 'failed'
            value = 'Application could not be verified'
        else:
            if is_username_exists(data['username']):  # Check if user name already exists
                message = 'failed'
                value = 'Username already exists'
                logging.error('Username already exists')
            else:
                if is_email_exists(data['email']):  # Check if email already exists
                    message = 'failed'
                    value = 'Email already exists'
                    logging.error('Email already exists')
                else:

                    # Create new django user
                    new_user = User.objects.create_user(data['username'],
                                                        data['email'],
                                                        data['password'])
                    new_user.first_name = data['first_name']
                    new_user.last_name = data['last_name']

                    logging.info("Setting up MQTT broker db info")
                    # Generate a random password
                    new_password = generate_random_pass()
                    # Do hash on the new password
                    hashed_pass = hash_password(new_password)

                    user_id = User.objects.get(username=data['username']).pk
                    insert_new_customer_to_mosquitto(user_id, data['email'])

                    # Add new "device" (customer) to the devices table
                    insert_new_client_to_devices(data['username'], hashed_pass, ip)
                    # Insert the customer into 'acls' table, with topic of: email/#
                    insert_into_acls_mosquitto_db(data['username'], data['username'] + "/#")

                    # Set new user as NOT active
                    new_user.is_active = False

                    new_user.save()

                    logging.info("Setting up verification process")
                    EmailVerification.objects.create(user=new_user)

                    message = 'success'
                    value = 'Registered!'
                    logging.info("success Registered!")
        return Response(build_json_response(message, value), status=status.HTTP_201_CREATED)


class DeviceActivationView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DeviceActivationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
            logging.info("New DeviceActivation request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logging.info("Request Parameters: " + str(data))

            device_id = data['device_id']
            device_name = data['device_name']

            if not is_device_id_exists(device_id):
                message = 'failed'
                value = 'Device does not exists'
                logging.error("Device does not exists")
            else:
                # Get token from request
                token = request.auth
                user_name = token.user
                user_id = token.user_id

                logging.info("Current logged in user name: " + str(user_name) + " ID is: " + str(user_id))

                # Check if the activated device is new (never got activated)
                # or the original username is activating his device again
                if not get_device_owner(device_id, user_id):
                    message = 'failed'
                    value = 'Device already associated'
                    logging.error("Device already associated")
                else:
                    logging.info("All checks passed, activating device")

                    # Insert the device into 'customer_devices' table
                    insert_into_customer_devices(user_id, device_id, device_name)
                    logging.info("insert_into_customer_devices completed")

                    # Build the topic, combined with userId + deviceId
                    topic = device_id + "/#"
                    # Insert the device into 'acls' table
                    insert_into_acls_mosquitto_db(device_id, topic)
                    insert_into_acls_mosquitto_db(user_name, topic)
                    logging.info("insert_into_acls_mosquitto_db completed")

                    message = 'success'
                    value = 'Activation successfully completed'
            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class DeviceListView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # Print request to log file
        logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
        logging.info("New DeviceList request at: " + str(datetime.datetime.now()))

        token = request.auth
        user_name = token.user
        user_id = token.user_id

        device_list = get_customers_devices(user_id)  # Get list of devices from the DB
        if not device_list:
            message = 'failed'
            value = 'no devices found'
            logging.info('No devices found')
        else:
            message = 'success'
            logging.info("Username: " + str(user_name) + " Devices found: " + str(device_list))

            json_array = []
            # Build Json array from the 'device_list' response from the DB
            for device in device_list:
                device_id = device[0]
                device_name = device[1]
                device_type = device[2]
                tmp_json = {"device_id": device_id, "device_name": device_name, "device_type": device_type}

                json_array.append(tmp_json)  # Append current details (device) to the array
            value = json_array  # Set the final json array to 'value'

        return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = ()

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
            logging.info("New ForgotPassword request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logging.info("Request Parameters: " + str(data))

            client_secret = data['client_secret']

            ip = get_real_ip(request)
            if ip is not None:
                logging.error('Could not detect IP of request')
                ip = 'none'

            # Get CLIENT_SECRET from DB ( if user is using a verified software
            if not get_client_secret_web_db(client_secret):
                message = 'failed'
                value = 'Application could not be verified'
            else:
                if not is_email_exists(data['email']):  # Check if email exists
                    logging.error("Error, email does not exist")
                    # Notify user all went OK
                    message = 'success'
                    value = 'Forgot Password Process completed'
                else:
                    # If all passed OK
                    form = PasswordResetForm(data)
                    if form.is_valid():
                        logging.info("Forgot password form is valid")

                        form.save(request=request)
                    else:
                        logging.info("Forgot password form is NOT valid")

                    logging.info("Success, Email sent to: " + data['email'])
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
            logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
            logging.info("New GetDevicePass request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logging.info("Request Parameters: " + str(data))

            device_id = data['device_id']

            if not is_device_id_exists(device_id):
                message = 'failed'
                value = 'Device does not exists'
                logging.info("Device does not exists")
            else:
                # Get token from request
                token = request.auth
                user_name = token.user
                user_id = token.user_id

                logging.info("Current logged in user name: " + str(user_name) + " ID is: " + str(user_id))

                # Now check if the activated device is new (never got activated)
                # or the original username is activating his device again
                if not get_device_owner(device_id, user_id):
                    message = 'failed'
                    value = 'Device already associated'
                    logging.info("Device already associated")
                else:
                    logging.info("All checks passed, generating hashed pass")
                    # Generate the password (8 characters long mixed digits with letters)
                    # The 'newPassword' should be returned to the app
                    new_password = generate_random_pass()
                    logging.info("New password generated: " + new_password)

                    # Do hash on the new password
                    hashed_pass = hash_password(new_password)
                    logging.info("Password has been hashed: " + hashed_pass)

                    # update the hashed pass into the DB,
                    # send device ID, hashed pass and the device name that the user choose
                    update_device_pass_mosquitto_db(device_id, hashed_pass)
                    logging.info("Password updated")

                    # Set success values
                    message = 'success'
                    value = new_password

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class GetScheduledJobView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # Print request to log file
        logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
        logging.info("New GetScheduledJob request at: " + str(datetime.datetime.now()))

        token = request.auth
        user_name = token.user
        user_id = token.user_id

        # TODO Write 'get scheduled jobs logic
        # If all passed OK return job id (value)
        logging.info("Success, scheduled job passed OK")
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
            logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
            logging.info("New RemoveDevice request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logging.info("Request Parameters: " + str(data))

            device_id = data['device_id']

            # Get token from request
            token = request.auth
            user_name = token.user
            user_id = token.user_id

            logging.info("Current logged in user name: " + str(user_name) + " ID is: " + str(user_id))

            if not get_device_owner(device_id, user_id):
                message = 'failed'
                value = 'You cannot remove this device'
                logging.error("User is not the device owner")
            else:
                remove_from_customer_devices(user_id, device_id)

                remove_from_acls(user_name, device_id + '%')
                remove_from_acls(device_id, device_id + '%')

                # Update device pass with some random pass
                new_password = generate_random_pass()
                logging.info("new password generated: " + new_password)

                # Do hash on the new password
                hashed_pass = hash_password(new_password)
                logging.info("Password has been hashed: " + hashed_pass)

                # update the hashed pass into the DB,
                # send device ID, hashed pass and the device name that the user choose
                update_device_pass_mosquitto_db(device_id, hashed_pass)

                logging.info("Password updated")

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
            logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
            logging.info("New ResetPassword request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logging.info("Request Parameters: " + str(data))

            current_password = data['current_password']
            new_password = data['new_password']

            # Get token from request
            token = request.auth
            user_name = token.user
            user_id = token.user_id

            logging.info("Current logged in user name: " + str(user_name) + " ID is: " + str(user_id))

            user_object = User.objects.get(id=user_id)

            if not user_object.check_password(current_password):
                message = 'failed'
                value = 'Current Password is incorrect'
                logging.info("Current Password '" + current_password + "' is incorrect")
            else:
                user_object.set_password(new_password)
                user_object.save()
                message = 'success'
                value = 'Password have been changed'
                logging.info("New password '" + new_password + "', Have been set successfully")

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class SetScheduledJobView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SetScheduledJobSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
            logging.info("New SetScheduledJob request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logging.info("Request Parameters: " + str(data))

            device_id = data['app_params']['device_id']

            # Get token from request
            token = request.auth
            user_name = token.user
            user_id = token.user_id

            logging.info("Current logged in user name: " + str(user_name) + " ID is: " + str(user_id))

            if not get_device_owner(device_id, user_id):
                message = 'failed'
                value = 'You cannot set new job for this device'
                logging.error("User is not the device owner")
            else:
                # This 'local_start_date' time, in this format:
                # datetime.datetime(2017, 5, 24, 11, 45, tzinfo=datetime.timezone(datetime.timedelta(0, 10800)))
                # the tzinfo represents a local GMT time
                # get start datetime object (local time) from json
                local_start_date = datetime.datetime.strptime(data["start_date_time_values"]["start_date_time_values"],
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
                end_date_time_selected = data['end_date_time_values']['end_date_time_selected']  # Boolean var
                # This 'local_end_date' time, in this format:
                # datetime.datetime(2017, 5, 24, 11, 45, tzinfo=datetime.timezone(datetime.timedelta(0, 10800)))
                # the tzinfo represents a local GMT time
                # get start datetime object (local time) from json
                local_end_date = datetime.datetime.strptime(data["end_date_time_values"]["end_date_time_values"],
                                                            '%Y-%m-%d %H:%M:%S%z')

                # This 'utc_date' time, in this format:
                # datetime.datetime(2017, 5, 31, 10, 4, tzinfo=<UTC>), In UTC time
                # Sent 'local_start_date' to the 'get_utc_datetime' function
                utc_end_date = get_utc_datetime(local_end_date)

                # Get the topic from json object, this topic will be used to send a message to
                topic_to_execute = data['app_params']['topic']

                # Execute the job, and get its job id into value
                value = schedule_new_job(device_id, topic_to_execute, is_repeated_job,
                                         days_to_repeat, job_action,
                                         end_date_time_selected, utc_start_date, utc_end_date)

                # If all passed OK return job id (value)
                logging.info("Success, scheduled job passed OK")
                message = 'success'

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class DelScheduledJobView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DeviceIdOnlySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
            logging.info("New DelScheduledJob request at: " + str(datetime.datetime.now()))

            data = serializer.data
            logging.info("Request Parameters: " + str(data))

            device_id = data['device_id']

            # Get token from request
            token = request.auth
            user_name = token.user
            user_id = token.user_id

            logging.info("Current logged in user name: " + str(user_name) + " ID is: " + str(user_id))

            # Get the job id that needs to be removed
            job_id = data['job_id']
            logging.info("job_id: " + job_id)

            # Start remove function from 'scheduler'
            remove_job_by_id(job_id)

            # If all passed OK return job id (value)
            logging.info("Success, scheduled job passed OK")
            message = 'success'
            value = 'job' + job_id + 'removed'

            return Response(build_json_response(message, value), status=status.HTTP_200_OK)


class UpdateMQTTUserPassView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        logging.basicConfig(filename=settings.BASE_DIR + '/logs/nalkinscloud_api.log', level=logging.DEBUG)
        logging.info("New UpdateMQTTUserPass request at: " + str(datetime.datetime.now()))

        # Get token from request
        token = request.auth
        user_name = token.user
        user_id = token.user_id

        logging.info("Current logged in user name: " + str(user_name) + " ID is: " + str(user_id))

        # If all passed OK, hash the token, and update customer "device" pass
        hashed_pass = hash_password(token)
        logging.info("Password has been hashed: " + hashed_pass)
        update_device_pass_mosquitto_db(user_name, hashed_pass)
        logging.info("Device: " + str(user_name) + " Hashed with pass: " + str(token))

        # Return user name
        message = 'success'
        value = str(user_name)

        return Response(build_json_response(message, value), status=status.HTTP_200_OK)


def verify_account(request, uuid):
    try:  # If incoming UUID exist in the db and is yet verified
        email_ver = EmailVerification.objects.get(verification_uuid=uuid, is_verified=False)
    except EmailVerification.DoesNotExist:
        raise Http404("User does not exist or is already verified")

    email_ver.is_verified = True
    email_ver.save()

    email_ver.user.is_active = True
    email_ver.user.save()

    return redirect('/verify_account_successful/')


def verify_account_successful(request):
    return render(
        request,
        BASE_DIR + '/templates/email_verification_success.html',
    )


def verify_account_failed(request):
    return render(
        request,
        BASE_DIR + '/templates/verification_failed.html',
    )


def index(request):

    return render(
        request,
        BASE_DIR + '/templates/index.html',
    )
