import logging
import datetime

from nalkinscloud_django.settings import BASE_DIR, PROJECT_NAME, VERSION, ENVIRONMENT
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout

from django_user_email_extension.models import verify_record

# Define logger
default_logger = logging.getLogger(PROJECT_NAME)

# Define global context values
context = {
    'project_name': PROJECT_NAME,
    'developer': 'Arie Lev',
    'current_year': datetime.datetime.now().year,
    'version': VERSION,
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
