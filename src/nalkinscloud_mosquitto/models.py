
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser

from django_user_email_extension.models import User


class DeviceTypeManager(models.Manager):
    def create_device_type(self, type_name):
        if not type_name:
            raise ValueError('Device type is mandatory')
        return self.create(type=type_name)


class DeviceType(models.Model):
    type = models.CharField(_('Device Type Name'), max_length=32, null=False, primary_key=True)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)

    def __str__(self):
        return self.type

    class Meta:
        verbose_name = _('device_type')
        verbose_name_plural = _('device_type')
        db_table = 'device_type'

    objects = DeviceTypeManager()


class DeviceModelManager(models.Manager):
    def create_device_model(self, model_name):
        if not model_name:
            raise ValueError('Device Model is mandatory')
        return self.create(model=model_name)


class DeviceModel(models.Model):
    model = models.CharField(_('Device Model Name'), max_length=32, null=False, primary_key=True)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)

    def __str__(self):
        return self.model

    class Meta:
        verbose_name = _('device_model')
        verbose_name_plural = _('device_model')
        db_table = 'device_model'

    objects = DeviceModelManager()


class DeviceManager(BaseUserManager):
    def create_device(self, device_id, password, **extra_fields):
        """
        Creates and saves a Device with the given device_id and password.
        """
        if not device_id:
            raise ValueError('Device id must be set')
        if not password:
            raise ValueError('Password must be set')
        device = self.model(device_id=device_id, **extra_fields)
        device.set_password(password)
        device.save()
        return device


class Device(AbstractBaseUser):
    device_id = models.CharField(_('Device Id'), max_length=32, null=False, primary_key=True)
    password = models.CharField(_('Password'), max_length=128, null=False)
    _password = None
    super = models.BooleanField(_('Super User'), default=False,)
    is_enabled = models.BooleanField(_('Device Enabled'), default=False,)
    model = models.ForeignKey(DeviceModel, on_delete=models.CASCADE, null=False)
    type = models.ForeignKey(DeviceType, on_delete=models.CASCADE, null=False)
    date_created = models.DateTimeField(_('Date Created'), auto_now_add=True, blank=True)
    last_update_date = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField('Connected From', null=True, blank=True)

    objects = DeviceManager()

    USERNAME_FIELD = 'device_id'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.device_id

    class Meta:
        verbose_name = _('device')
        verbose_name_plural = _('devices')
        db_table = 'devices'


class CustomerDevice(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.ForeignKey(Device, on_delete=models.CASCADE)
    device_name = models.CharField(_('Device Name'), max_length=32, null=False)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)

    def __str__(self):
        return self.user_id.email + ' <-> ' + self.device_id.device_id

    class Meta:
        unique_together = ('user_id', 'device_id',)  # Set primary combined key
        verbose_name = _('customer_device')
        verbose_name_plural = _('customer_device')
        db_table = 'customer_device'

    def get_user_id(self):
        return self.user_id


class AccessList(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    topic = models.CharField(_('Message Topic'), max_length=256, null=False)
    rw = models.IntegerField(_('Read Write Mode'),
                             validators=[MaxValueValidator(2), MinValueValidator(0)],
                             null=False,
                             default=1)
    is_enabled = models.BooleanField(_('ACL Enabled'), default=False)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)
    last_update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'device: ' + self.device.device_id + ' can access ' + self.topic

    class Meta:
        unique_together = (('device', 'topic'),)
        verbose_name = _('access_list')
        verbose_name_plural = _('access_list')
        db_table = 'access_list'


class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    topic = models.CharField(_('Message Topic'), max_length=256, null=False)
    message = models.CharField(_('Message Body'), max_length=256, null=False)
    qos = models.IntegerField(_('QOS'), validators=[MaxValueValidator(1), MinValueValidator(0)], null=False, default=1)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)

    def __str__(self):
        return 'Message of device: ' + self.device.device_id

    class Meta:
        verbose_name = _('messages')
        verbose_name_plural = _('messages')
        db_table = 'messages'
