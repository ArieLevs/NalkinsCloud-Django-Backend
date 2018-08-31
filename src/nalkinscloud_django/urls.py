from django.contrib import admin
from django.conf.urls import include, url
from django.urls import path

urlpatterns = [
    url(r'^', include('nalkinscloud_api.urls')),
    url(r'^', include('nalkinscloud_frontend.urls')),

    # OAUTH URLS
    url(r'^', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # Django auth urls
    url('^', include('django.contrib.auth.urls')),

    path('nalkinsadmin/', admin.site.urls),

]
