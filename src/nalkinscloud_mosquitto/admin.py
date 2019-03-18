from nalkinscloud_mosquitto.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from django.utils.translation import ugettext_lazy as _


@admin.register(DeviceType)
class CustomDevicesAdmin(admin.ModelAdmin):
    pass


@admin.register(DeviceModel)
class CustomDevicesAdmin(admin.ModelAdmin):
    pass


@admin.register(Device)
class CustomDevicesAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('device_id', 'password')}),
        (_('Device info'), {'fields': ('super', 'is_enabled', 'model', 'type')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('device_id', 'super', 'is_enabled', 'model', 'type', 'password1', 'password2')}
         ),
    )
    filter_horizontal = ()
    list_display = ('device_id', 'model', 'type', 'is_enabled', )
    list_filter = ('device_id',)
    search_fields = ('device_id', )
    ordering = ('device_id', )
    pass


@admin.register(CustomerDevice)
class CustomDevicesAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'device_id', 'device_name')
    ordering = ('user_id',)
    pass


@admin.register(AccessList)
class CustomDevicesAdmin(admin.ModelAdmin):
    list_display = ('device', 'topic', 'rw', 'is_enabled')
    ordering = ('device',)
    pass


@admin.register(Message)
class CustomDevicesAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'device', 'topic', 'message')
    ordering = ('device',)
    pass
