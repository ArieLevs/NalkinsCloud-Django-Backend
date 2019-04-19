from django.apps import AppConfig
import logging
from nalkinscloud_django.settings import PROJECT_NAME

# Define logger
logger = logging.getLogger(PROJECT_NAME)


class NalkinscloudMosquittoConfig(AppConfig):
    name = 'nalkinscloud_mosquitto'

    # def ready(self):
    #     logger.info("####################################################\n"
    #                 "Nalkinscloud Mosquitto Application is up and running\n"
    #                 "####################################################")
    #     pass
