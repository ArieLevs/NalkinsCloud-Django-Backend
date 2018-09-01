
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator

from django_user_email_extension.models import User
from django.contrib.auth.hashers import make_password


class DeviceType(models.Model):
    type = models.CharField(_('Device Type Name'), max_length=32, null=False, primary_key=True)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)

    def __str__(self):
        return self.type

    class Meta:
        verbose_name = _('device_type')
        verbose_name_plural = _('device_type')
        db_table = 'device_type'


class DeviceModel(models.Model):
    model = models.CharField(_('Device Model Name'), max_length=32, null=False, primary_key=True)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)

    def __str__(self):
        return self.model

    class Meta:
        verbose_name = _('device_model')
        verbose_name_plural = _('device_model')
        db_table = 'device_model'


class Devices(models.Model):
    device_id = models.CharField(_('Device Id'), max_length=32, null=False, primary_key=True)
    password = models.CharField(_('Password'), max_length=128, null=False)
    _password = None
    super = models.IntegerField(_('Super User'),
                                validators=[MaxValueValidator(1), MinValueValidator(0)],
                                null=False,
                                default=0)
    is_enabled = models.IntegerField(_('User Enabled'),
                                     validators=[MaxValueValidator(1), MinValueValidator(0)],
                                     null=False,
                                     default=0)
    model = models.ForeignKey(DeviceModel, on_delete=models.CASCADE)
    type = models.ForeignKey(DeviceType, on_delete=models.CASCADE)
    date_created = models.DateTimeField(_('Date Created'), auto_now_add=True, blank=True)
    last_update_date = models.DateTimeField(auto_now=True)
    last_connection = models.DateTimeField(blank=True, null=True)
    last_connection_ip = models.GenericIPAddressField('Connected From', null=True, blank=True)

    def save(self, *args, **kwargs):
        self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.device_id

    class Meta:
        verbose_name = _('devices')
        verbose_name_plural = _('devices')
        db_table = 'devices'


class CustomerDevice(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.ForeignKey(Devices, on_delete=models.CASCADE)
    device_name = models.CharField(_('Device Name'), max_length=32, null=False)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)

    def __str__(self):
        return 'Device of customer: ' + self.user_id.email

    class Meta:
        # unique_together = ('user_id', 'device_id',)  # Set primary combined key
        verbose_name = _('customer_device')
        verbose_name_plural = _('customer_device')
        db_table = 'customer_device'

    def get_user_id(self):
        return self.user_id


class AccessList(models.Model):
    device = models.OneToOneField(Devices, on_delete=models.CASCADE)
    topic = models.CharField(_('Message Topic'), max_length=256, null=False)
    rw = models.IntegerField(_('Read Write Mode'),
                             validators=[MaxValueValidator(2), MinValueValidator(0)],
                             null=False,
                             default=1)
    is_enabled = models.IntegerField(_('ACL Enabled'),
                                     validators=[MaxValueValidator(1), MinValueValidator(0)],
                                     null=False,
                                     default=1)
    date_created = models.DateTimeField(_('Date Created'),  auto_now_add=True, blank=True)
    last_update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'ACL of device: ' + self.device.device_id

    class Meta:
        unique_together = ('device', 'topic')
        verbose_name = _('access_list')
        verbose_name_plural = _('access_list')
        db_table = 'access_list'


class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    device = models.ForeignKey(Devices, on_delete=models.CASCADE)
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
