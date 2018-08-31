
from django.contrib import admin
from nalkinscloud_api.models import User, EmailVerification


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(EmailVerification)
class UserAdmin(admin.ModelAdmin):
    pass
