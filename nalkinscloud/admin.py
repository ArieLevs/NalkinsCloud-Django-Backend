
from django.contrib import admin
from .models import EmailVerification


@admin.register(EmailVerification)
class UserAdmin(admin.ModelAdmin):
    pass
