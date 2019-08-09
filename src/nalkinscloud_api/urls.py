from django.conf.urls import url

from . import views_api
from . import views

app_mame = "web_api"

urlpatterns = [
    url(r'^$', views.index, name='index'),

    # General
    url(r'^login_page/', views.login_page, name='login_page'),
    url(r'^logout_process/', views.logout_process, name='logout_process'),

    # Email verifications urls
    url(r'^verify_account/(?P<uuid>[a-z0-9\-]+)/', views.verify_account, name='verify_account'),
    url(r'^verify_account_successful/', views.verify_account_successful, name='verify_account_successful'),
    url(r'^verify_account_failed/', views.verify_account_failed, name='verify_account_failed'),

    # REST API urls
    url(r'^readiness/', views_api.ReadinessProbe.as_view(), name='readiness'),
    url(r'^liveness/', views_api.LivenessProbe.as_view(), name='liveness'),
    url(r'^register/', views_api.RegistrationView.as_view(), name='register'),
    url(r'^health_check/', views_api.HealthCheckView.as_view(), name='health_check'),  # Auth require
    url(r'^device_activation/', views_api.DeviceActivationView.as_view(), name='device_activation'),  # Auth require
    url(r'^device_list/', views_api.DeviceListView.as_view(), name='device_list'),  # Auth require
    url(r'^forgot_password/', views_api.ForgotPasswordView.as_view(), name='forgot_password'),
    url(r'^get_device_pass/', views_api.GetDevicePassView.as_view(), name='get_device_pass'),  # Auth require
    url(r'^get_scheduled_job/', views_api.GetScheduledJobView.as_view(), name='get_scheduled_job'),  # Auth require
    url(r'^remove_device/', views_api.RemoveDeviceView.as_view(), name='remove_device'),  # Auth require
    url(r'^reset_password/', views_api.ResetPasswordView.as_view(), name='reset_password'),  # Auth require
    url(r'^set_scheduled_job/', views_api.SetScheduledJobView.as_view(), name='set_scheduled_job'),  # Auth require
    url(r'^del_scheduled_job/', views_api.DelScheduledJobView.as_view(), name='del_scheduled_job'),  # Auth require
    url(r'^update_device_pass/', views_api.UpdateMQTTUserPassView.as_view(), name='update_device_pass'),  # Auth require
]
