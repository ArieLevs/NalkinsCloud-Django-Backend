
from django.db import models

import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

from nalkinscloud_django.settings import DOMAIN_NAME, EMAIL_HOST_USER


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Email must be set')
        if not password:
            raise ValueError('Password must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, primary_key=True)
    user_name = models.CharField(_('User Name'), max_length=128, blank=True)
    first_name = models.CharField(_('First Name'), max_length=32, blank=True)
    last_name = models.CharField(_('Last Name'), max_length=32, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    address = models.TextField(max_length=500, default='', blank=True)
    city = models.CharField(max_length=30, default='', blank=True)
    country = models.CharField(max_length=30, default='', blank=True)
    postal_code = models.IntegerField(blank=True, default=00000)

    registration_ip = models.GenericIPAddressField('Registered From', null=True)
    language = models.CharField(_('Users Language'), max_length=2, null=False, default='EN')

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this site.'),
    )
    is_active = models.BooleanField(
        _('Active Status'),
        default=True,
        help_text=_('Define if this user should be treated as active. '),
    )
    date_created = models.DateTimeField('Date Created', auto_now_add=True, blank=True)
    last_update_date = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(default=None, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField('Logged in from', default=None, blank=True, null=True)

    USERNAME_FIELD = 'email'
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_first_name(self):
        return self.first_name

    def get_last_name(self):
        return self.last_name


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField('verified', default=False)
    verification_uuid = models.UUIDField('Unique Verification UUID', default=uuid.uuid4)

    def __str__(self):
        return 'Email Verification for User: ' + self.user.get_username()


@receiver(post_save, sender=EmailVerification, dispatch_uid="verify new account")
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
