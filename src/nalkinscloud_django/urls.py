from django.contrib import admin
from django.conf.urls import include, url
from django.urls import path

urlpatterns = [
    url(r'^', include('nalkinscloud_ui.urls')),

    # api urls
    path('api/', include('nalkinscloud_api.urls')),

    # OAUTH URLS
    url(r'^', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # Django auth urls
    url('^', include('django.contrib.auth.urls')),
    # Social auth urls
    url('', include('social_django.urls', namespace='social')),

    path('nalkinsadmin/', admin.site.urls),
]
