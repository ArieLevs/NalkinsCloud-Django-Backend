
from django.apps import AppConfig
import logging
from nalkinscloud_django.settings import PROJECT_NAME

# Define logger
logger = logging.getLogger(PROJECT_NAME)


class NalkinsCloudAPIConfig(AppConfig):
    name = 'nalkinscloud_api'

    # def ready(self):
    #     logger.info("#################################\n"
    #                 "Nalkinscloud API is up and running\n"
    #                 "#################################")
    #     pass
