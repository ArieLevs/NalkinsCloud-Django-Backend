
from django.apps import AppConfig
from django.conf import settings


class NalkinsCloudAPIConfig(AppConfig):
    name = settings.APP_NAME

    # def ready(self):
    #     logger.info("#################################\n"
    #                 "Nalkinscloud API is up and running\n"
    #                 "#################################")
    #     pass
