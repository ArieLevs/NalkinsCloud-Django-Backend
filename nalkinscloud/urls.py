from django.conf.urls import url

from . import views, views_api
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView

urlpatterns = [
    # REST API urls
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

    url(r'^verify_account/(?P<uuid>[a-z0-9\-]+)/', views.verify_account, name='verify_account'),
    url(r'^verify_account_successful/', views.verify_account_successful, name='verify_account_successful'),
    url(r'^verify_account_failed/', views.verify_account_failed, name='verify_account_failed'),

    url(r'^$', views.index, name='index'),
    url(r'^login/', views.login_page, name='login_page'),
    url(r'^login_process/', views.login_process, name='login_process'),
    url(r'^logout_process/', views.logout_process, name='logout_process'),
    url(r'^dashboard/', views.dashboard, name='dashboard'),

    # Pass reset views
    url(r'^password_reset/$', auth_views.password_reset),
    url(r'^password_reset/done/$', views.verify_account_successful, name='sdfsdf'),
    url(r'^reset/done/$', auth_views.password_reset_complete, name='password_reset_complete'),

    #url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),
    #url(r'^$', TemplateView.as_view(template_name='login.html'), name="login"),
]
