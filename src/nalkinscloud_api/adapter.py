from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.admin import EmailAddress


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapted needs to be used since we use custom user model
    django_user_email_extension model, when creating new user, by default its 'is_active' is False
    https://django-allauth.readthedocs.io/en/latest/configuration.html
    """
    def save_user(self, request, sociallogin, form=None):
        social_user = super(CustomSocialAccountAdapter, self).save_user(request, sociallogin, form)
        verified_mail = EmailAddress.objects.filter(email=social_user, verified=True).exists()

        if verified_mail:
            social_user.is_active = True
        social_user.save()

        return social_user
