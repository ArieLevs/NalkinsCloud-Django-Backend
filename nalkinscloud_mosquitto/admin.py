from nalkinscloud_mosquitto.models import *
from django.contrib import admin


@admin.register(DeviceType)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(DeviceModel)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Devices)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(CustomerDevice)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(AccessList)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Message)
class UserAdmin(admin.ModelAdmin):
    pass

