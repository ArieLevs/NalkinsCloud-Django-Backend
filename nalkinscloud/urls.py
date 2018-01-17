from django.conf.urls import url

from . import views

urlpatterns = [
    # REST API urls
    url(r'^register/', views.RegistrationView.as_view(), name='register'),
    url(r'^health_check/', views.HealthCheckView.as_view(), name='health_check'),  # Auth require
    url(r'^device_activation/', views.DeviceActivationView.as_view(), name='device_activation'),  # Auth require
    url(r'^device_list/', views.DeviceListView.as_view(), name='device_list'),  # Auth require
    url(r'^forgot_password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    url(r'^get_device_pass/', views.GetDevicePassView.as_view(), name='get_device_pass'),  # Auth require
    url(r'^get_scheduled_job/', views.GetScheduledJobView.as_view(), name='get_scheduled_job'),  # Auth require
    url(r'^remove_device/', views.RemoveDeviceView.as_view(), name='remove_device'),  # Auth require
    url(r'^reset_password/', views.ResetPasswordView.as_view(), name='reset_password'),  # Auth require
    url(r'^set_scheduled_job/', views.SetScheduledJobView.as_view(), name='set_scheduled_job'),  # Auth require
    url(r'^del_scheduled_job/', views.DelScheduledJobView.as_view(), name='del_scheduled_job'),  # Auth require
    url(r'^update_device_pass/', views.UpdateMQTTUserPassView.as_view(), name='update_device_pass'),  # Auth require
    url(r'^verify_account/(?P<uuid>[a-z0-9\-]+)/', views.verify_account, name='verify_account'),
    url(r'^verify_account_successful/', views.verify_account_successful, name='verify_account_successful'),
    url(r'^verify_account_failed/', views.verify_account_failed, name='verify_account_failed'),

    url(r'^$', views.index, name='index'),
]
