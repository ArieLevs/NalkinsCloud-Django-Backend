from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('nalkinscloud_ui.urls')),

    # api urls
    path('api/', include('nalkinscloud_api.urls')),

    # OAUTH URLS
    path('', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # Django auth urls
    path('', include('django.contrib.auth.urls')),

    # all auth
    path('accounts/', include('allauth.urls')),

    path('nalkinsadmin/', admin.site.urls),
]
