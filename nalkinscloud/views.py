import logging
import datetime

from nalkinscloud.functions import *
from django.conf import settings
from django.shortcuts import render, redirect

from nalkinscloud.models import EmailVerification

# REST Framework
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect


# Define global context values
context = {'project_name': 'NalkinsCloud',
           'developer': 'Arie Lev',
           'current_year': datetime.datetime.now().year}  # Pass year to template


def verify_account(request, uuid):
    try:  # If incoming UUID exist in the db and is yet verified
        email_ver = EmailVerification.objects.get(verification_uuid=uuid, is_verified=False)
    except EmailVerification.DoesNotExist:
        return redirect('/verify_account_failed/')

    # If above verification uuid found then set main to verified
    email_ver.is_verified = True
    email_ver.save()

    # And set account is active status
    email_ver.user.is_active = True
    email_ver.user.save()

    return redirect('/verify_account_successful/')


def verify_account_successful(request):
    return render(
        request,
        BASE_DIR + '/templates/registration/email_verification_success.html',
        context,
        status=status.HTTP_200_OK,
    )


def verify_account_failed(request):
    return render(
        request,
        BASE_DIR + '/templates/registration/verification_failed.html',
        context,
        status=status.HTTP_200_OK,
    )


# Render main index page
def index(request):
    return render(
        request,
        BASE_DIR + '/templates/index.html',
        context,
        status=status.HTTP_200_OK,
    )


def login_page(request):
    if request.user.is_authenticated:  # If authenticated send user to dashboard
        return HttpResponseRedirect('/dashboard/')
    else:  # Else render login page
        return render(
            request,
            BASE_DIR + '/templates/dashboard/login.html',
            context,
            status=status.HTTP_200_OK,
        )


def login_process(request):
    logging.basicConfig(filename=settings.BASE_DIR + '/logs/login.log', level=logging.DEBUG)
    logging.info("New login_process request at: " + str(datetime.datetime.now()))
    logging.info(str(request))

    if request.POST:
        logging.info("POST request received, moving on")
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            logging.info("User: " + str(user) + " Authenticated, moving on")
            if user.is_active:
                logging.error("User: " + str(user) + " Is active, perform login")
                login(request, user)
                return HttpResponseRedirect('/dashboard/')
            else:
                logging.error("User: " + str(user) + " Is not active, stop login, show error context")
                context.update({'error': 'User is not active, please make sure your email was verified'})
                return_code = status.HTTP_401_UNAUTHORIZED
        else:
            logging.error("Username could not be authenticated, stop login, show error context")
            context.update({'error': 'Username could not be authenticated'})
            return_code = status.HTTP_401_UNAUTHORIZED
    else:
        logging.error("no POST received, stop login")
        context.update({'error': 'Bad request'})
        return_code = status.HTTP_400_BAD_REQUEST
    return render(
        request,
        BASE_DIR + '/templates/dashboard/login.html',
        context,
        status=return_code,
    )


def logout_process(request):
    logging.basicConfig(filename=settings.BASE_DIR + '/logs/logout.log', level=logging.DEBUG)
    logging.info("logout_process request at: " + str(datetime.datetime.now()) + "by user" + str(request.user))

    logout(request)
    return HttpResponseRedirect('/')


def dashboard(request):
    logging.basicConfig(filename=settings.BASE_DIR + '/logs/index.log', level=logging.DEBUG)
    logging.info("login_process request at: " + str(datetime.datetime.now()))
    logging.info(str(request))

    user_name = None

    if request.user.is_authenticated:  # First check if user is authenticated
        user_name = request.user.user_name
        logging.info("User - " + user_name + " entering dashboard")

        context.update({'username': user_name})
        return render(
            request,
            BASE_DIR + '/templates/dashboard/index.html',
            context,
            status=status.HTTP_200_OK
        )
    else:
        logging.error("User - " + str(user_name) + " is not authenticated")
        return HttpResponseRedirect('/login/')
