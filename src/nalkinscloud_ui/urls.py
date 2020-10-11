from django.urls import path, re_path

from nalkinscloud_ui import views

app_name = 'nalkinscloud_ui'

urlpatterns = [
    re_path(r'^$', views.index, name='index'),

    # General
    path('login_page/', views.login_page, name='login_page'),
    path('login_process/', views.login_process, name='login_process'),
    path('logout_process/', views.logout_process, name='logout_process'),

    # Email verifications urls
    path('verify_account/<uuid:verification_uuid>/', views.VerifyEmailUUIDView.as_view(), name='verify_account'),

    path('devices/', views.devices_view, name='devices')
]
