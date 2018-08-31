import os
import ssl
from celery import Celery
from django.conf import settings
from django_server.settings import CELERY_REDIS_URL
from paho import *

MOSQUITTO_BROKER_URL = 'mqtt://test_distillery_deviceid:XFXWLRA1@10.99.0.111:1884'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_server.settings')

app = Celery('django_server',
             backend=CELERY_REDIS_URL,
             broker=MOSQUITTO_BROKER_URL)


# app.connection(hostname='10.99.0.111', port=1884, userid='test_dht_deviceid', password='XFXWLRA1')

'''app.conf.BROKER_USE_SSL = {
    'ca_certs': '/etc/certs/mosquitto_ca.crt',
    'keyfile': '/etc/certs/mosquitto_server.key',
    'certfile': '/etc/certs/mosquitto_server.crt',
    'cert_reqs': ssl.CERT_REQUIRED
}


app.conf.update(
    security_key='/etc/certs/mosquitto_server.key',
    security_certificate='/etc/certs/mosquitto_server.crt',
    security_cert_store='/etc/certs/*.pem')
app.setup_security()'''

app.config_from_object('django.conf:settings')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
