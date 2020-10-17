import logging

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout, authenticate, login
from django.views.generic import UpdateView, ListView
from django.contrib import messages

from django_user_email_extension.models import DjangoEmailVerifier
from django_user_email_extension.forms import VerificationUUIDForm

from nalkinscloud_mosquitto.models import CustomerDevice

# Define logger
default_logger = logging.getLogger(__name__)


# Render main index page
def index(request):
    return render(
        request,
        template_name='index.html',
        status=HttpResponse.status_code,
    )


class VerifyEmailUUIDView(UpdateView):
    form_class = VerificationUUIDForm
    model = DjangoEmailVerifier
    template_name = 'email_verification/email_verification_complete.html'

    slug_field = 'verification_uuid'
    slug_url_kwarg = 'verification_uuid'

    def get(self, request, *args, **kwargs):
        verification_uuid = self.get_object()

        try:
            verification_uuid.verify_record()
            messages.error(self.request, "successfully verified email: {}".format(verification_uuid.email))
        except Exception as e:
            # in case of exception, add returned message from verify_record()
            messages.error(self.request, "{}".format(e))

        return super().get(request, *args, **kwargs)


class DevicesListView(ListView):
    # set context object name, template will iterate over this object
    context_object_name = "device_list"
    template_name = 'devices.html'
    page_title = 'User Devices'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('page_title', self.page_title)
        return context

    def get_queryset(self):
        return CustomerDevice.objects.filter(user_id=self.request.user)


def logout_process(request):
    default_logger.info("logout_process request by user: " + str(request.user))
    logout(request)
    return HttpResponseRedirect('/')


def login_page(request):
    default_logger.info("login_page request")
    default_logger.info(request)

    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    else:
        return render(
            request,
            template_name='login.html',
            status=HttpResponse.status_code,
        )


def login_process(request):
    default_logger.info("login_process request")
    default_logger.info(str(request))

    context = {}

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
                context.update({'error': 'User is not active, please make sure your email was verified'})
        else:
            default_logger.error("email could not be authenticated, stop login, show error context")
            context.update({'error': 'email could not be authenticated'})
    else:
        default_logger.error("no post received, stop login")
        context.update({'error': 'bad request'})

    return render(
        request,
        template_name='login.html',
        context=context,
        status=HttpResponse.status_code
    )