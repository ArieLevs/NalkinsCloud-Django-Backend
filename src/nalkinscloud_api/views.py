import logging
import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout, authenticate, login

from django_user_email_extension.models import verify_record

from nalkinscloud_mosquitto.functions import get_customers_devices
from nalkinscloud_django.settings import BASE_DIR, PROJECT_NAME, VERSION, HOSTNAME, ENVIRONMENT,\
    MQTT_BROKER_HOST, MQTT_BROKER_PORT

# Define logger
default_logger = logging.getLogger(PROJECT_NAME)

# Define global context values
context = {
    'project_name': PROJECT_NAME,
    'developer': 'Arie Lev',
    'current_year': datetime.datetime.now().year,
    'version': VERSION,
    'hostname': HOSTNAME,
    'environment': ENVIRONMENT,
}


# Render main index page
def index(request):
    default_logger.info("index request at: " + str(datetime.datetime.now()))
    default_logger.info(request)

    return render(
        request,
        BASE_DIR + '/templates/index.html',
        context,
        status=HttpResponse.status_code,
    )


def verify_account(request, uuid):

    default_logger.info("verify_account request at: " + str(datetime.datetime.now()))
    default_logger.info(request)

    try:
        if verify_record(uuid_value=uuid):
            return redirect('/verify_account_successful/')
    except Exception as e:
        default_logger.info(e)
        pass

    return redirect('/verify_account_failed/')


def verify_account_successful(request):
    default_logger.info("verify_account_successful request at: " + str(datetime.datetime.now()))
    default_logger.info(request)

    return render(
        request,
        BASE_DIR + '/templates/email_verification/email_verification_success.html',
        context,
        status=HttpResponse.status_code,
    )


def verify_account_failed(request):
    default_logger.info("verify_account_failed request at: " + str(datetime.datetime.now()))
    default_logger.info(request)

    return render(
        request,
        BASE_DIR + '/templates/email_verification/email_verification_failed.html',
        context,
        status=HttpResponse.status_code,
    )


def logout_process(request):
    default_logger.info("logout_process request at: " + str(datetime.datetime.now()) + " by user: " + str(request.user))

    logout(request)
    return HttpResponseRedirect('/')


def login_page(request):
    default_logger.info("login_page request at: " + str(datetime.datetime.now()))
    default_logger.info(request)

    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    else:
        return render(
            request,
            BASE_DIR + '/templates/login.html',
            context,
            status=HttpResponse.status_code,
        )


def login_process(request):
    default_logger.info("login_process request at: " + str(datetime.datetime.now()))
    default_logger.info(str(request))

    temp_context = context.copy()

    if request.POST:
        default_logger.info("post request received, moving on")
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:
            default_logger.info("user: " + str(user) + " Authenticated, moving on")
            if user.is_active:
                default_logger.error("user: " + str(user) + " is active, perform login")
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                default_logger.error("user: " + str(user) + " is not active, stop login, show error context")
                temp_context.update({'error': 'User is not active, please make sure your email was verified'})
        else:
            default_logger.error("email could not be authenticated, stop login, show error context")
            temp_context.update({'error': 'email could not be authenticated'})
    else:
        default_logger.error("no post received, stop login")
        temp_context.update({'error': 'bad request'})

    return render(
        request,
        BASE_DIR + '/templates/login.html',
        temp_context,
        status=HttpResponse.status_code
    )


@login_required
def devices_view(request):
    default_logger.info("devices_view request at: " + str(datetime.datetime.now()))
    temp_context = context.copy()
    temp_context.update({'broker_host': MQTT_BROKER_HOST, 'broker_port': MQTT_BROKER_PORT})

    device_list = get_customers_devices(request.user)

    if not device_list:
        default_logger.info('no devices found')
    else:
        default_logger.info("user: " + str(request.user.email) + " devices found: " + str(device_list))

        json_array = []
        # Build Json array from the 'device_list' response from the DB
        for device in device_list:
            device_id = str(device.device_id)
            device_name = str(device.device_name)
            device_type = str(device.device_id.type)

            tmp_json = {"device_id": device_id, "device_name": device_name, "device_type": device_type}

            json_array.append(tmp_json)  # Append current details (device) to the array
        temp_context.update({'device_list': json_array})

    print('current context: ' + str(temp_context))
    return render(
        request,
        BASE_DIR + '/templates/devices.html',
        temp_context,
        status=HttpResponse.status_code
    )
