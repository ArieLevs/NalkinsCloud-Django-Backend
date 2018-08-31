import logging
from django.utils import timezone
from django.conf import settings

from django.db import models

import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.urls import reverse

from nalkinscloud_django.settings import DOMAIN_NAME, EMAIL_HOST_USER


class DjangoEmailVerifierUsage(object):

    def verify_email(self, uuid_value):
        address = self.user.verify_record(uuid_value)
        return address.email


class DjangoEmailVerifierManger(models.Manager):

    def create_verification(self, email, user=None):
        # if User model have email field
        if settings.AUTH_USER_MODEL.field_exists('email'):
            user = user
        self.create(user=user)

    def verify_record(self, uuid_value):
        # If input UUID exist in the db
        try:
            email_ver_object = self.get(verification_uuid=uuid_value, is_verified=False)
        except DjangoEmailVerifier.DoesNotExist:
            raise Exception("Error - %s not associated to any email", uuid_value)

        if email_ver_object.is_uuid_expired:
            raise Exception("Error - %s expired", uuid_value)

        # If current object yet verified
        if not email_ver_object.verified:
            email_ver_object.is_verified = True
            email_ver_object.verified_at = timezone.now()
            email_ver_object.save()

        # And set account is active status if User model have one
        if settings.AUTH_USER_MODEL.field_exists('is_active'):
            email_ver_object.user.is_active = True
            email_ver_object.user.save()

        return True

    # @classmethod
    # def model_field_exists(cls, field):
    #     try:
    #         cls._meta.get_field(field)
    #         return True
    #     except models.FieldDoesNotExist:
    #         return False
    #
    # models.Model.field_exists = model_field_exists
    # if settings.AUTH_USER_MODEL.field_exists('is_active'):


class DjangoEmailVerifier(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255)
    is_verified = models.BooleanField('verified', default=False)
    verification_uuid = models.UUIDField('Unique Verification UUID', default=uuid.uuid4)
    date_created = models.DateTimeField('Date Created', auto_now_add=True, blank=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    objects = DjangoEmailVerifierManger()

    def __str__(self):
        return 'Email Verification for User: ' + self.user.get_username()

    @property
    def verified(self):
        return self.is_verified

    @property
    def uuid_expire_date(self):
        # Only if DJANGO_EMAIL_VERIFIER_EXPIRE_TIME is not None,
        # Else, uuid never expire.
        # Set example: DJANGO_EMAIL_VERIFIER_EXPIRE_TIME=''
        time_to_expire = getattr(settings, 'SIMPLE_EMAIL_CONFIRMATION_PERIOD', None)
        return self.date_created + time_to_expire if time_to_expire is not None else None

    @property
    def is_uuid_expired(self):
        return self.uuid_expire_date and timezone.now() >= self.uuid_expire_date


@receiver(post_save, sender=DjangoEmailVerifier, dispatch_uid="verify new account")
def send_verification_email(sender, instance, signal, *args, **kwargs):
    if not instance.is_verified:
        # Send verification email
        send_mail(
            'Verify your NalkinsCloud account',  # Subject
            'Follow this link to verify your account: '  # Body
            + DOMAIN_NAME + '%s' % reverse('verify_account', kwargs={'uuid': str(instance.verification_uuid)}),
            EMAIL_HOST_USER,  # From
            [instance.user.email],  # To
            fail_silently=False,
        )
