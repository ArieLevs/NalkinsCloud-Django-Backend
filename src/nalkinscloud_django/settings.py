
import os

ENVIRONMENT = os.environ.get('environment', 'dev')

BACKEND_DOMAIN = os.environ.get('backend_domain', 'http://127.0.0.1:8000')
FRONTEND_DOMAIN = os.environ.get('frontend_domain', 'http://127.0.0.1:8000')

PROJECT_NAME = 'nalkinscloud-api'
VERSION = os.environ.get('version', 'null')
EXTRA_ALLOWED_HOSTS = os.environ.get('allowed_hosts', '').split(',')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('django_secret_key', 'djangoSecretKey')

# SECURITY WARNING: don't run with debug turned on in production!
if ENVIRONMENT == 'dev':
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = ['api.nalkinscloud.localhost',
                 'alpha.api.nalkins.cloud',
                 'api.nalkins.cloud',
                 '127.0.0.1',
                 '10.0.2.2' # Android AVD IP for localhost
                 ] + EXTRA_ALLOWED_HOSTS

# Application definition/etc/rc.d/
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'oauth2_provider',
    'rest_framework',
    'nalkinscloud_api',
    'nalkinscloud_mosquitto',
    'scheduler',
    'django_user_email_extension',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nalkinscloud_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nalkinscloud_django.wsgi.application'

######################
# DATABASE SETTINGS
######################
if ENVIRONMENT == 'dev':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('db_name', 'django'),
            'USER': os.environ.get('db_user', 'django'),
            'PASSWORD': os.environ.get('db_pass', 'django'),
            'HOST': os.environ.get('db_host', 'localhost'),
            'PORT': '3306',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'}
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

# URL to use when referring to static files
STATIC_URL = os.environ.get('static_url', "/static/")

# This setting defines the additional locations the staticfiles
STATICFILES_DIRS = []

# The absolute path to the directory where collectstatic will collect static files for deployment
if ENVIRONMENT == 'ci':
    STATIC_ROOT = os.environ.get('static_root', os.path.join(BASE_DIR, "static"))

FIXTURE_DIRS = (
   os.path.join(BASE_DIR, 'nalkinscloud_mosquitto/fixtures'),
)

######################
# Custom User Model
######################
AUTH_USER_MODEL = 'django_user_email_extension.User'

######################
# EMAIL SETTINGS
######################
EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('email_host')
EMAIL_PORT = os.environ.get('email_port')
EMAIL_HOST_USER = os.environ.get('email_username')
EMAIL_HOST_PASSWORD = os.environ.get('email_password')

DJANGO_EMAIL_VERIFIER_EXPIRE_TIME = 24  # In Hours

# REDIS related settings
REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
BROKER_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}

CELERY_REDIS_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT
CELERY_RESULT_BACKEND = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Jerusalem'
CELERY_BEAT_SCHEDULE = {}

######################
# LOGGING SETTINGS
######################
GRAYLOG_HOST = os.environ.get('graylog_host', None)
GRAYLOG_PORT = os.environ.get('graylog_port', 12201)

if ENVIRONMENT != 'dev' and GRAYLOG_HOST is not None:
    LOGGING = {
        'version': 1,
        'filters': {
            'fields': {
                '()': 'nalkinscloud_api.logging_filter.FieldFilter',
                'fields': {
                    'application': PROJECT_NAME,
                    'environment': ENVIRONMENT,
                },
            },
        },
        'handlers': {
            'gelf': {
                'class': 'graypy.GELFHandler',
                'host': GRAYLOG_HOST,
                'port': GRAYLOG_PORT,
                'filters': ['fields']
            },
        },

        'loggers': {
            PROJECT_NAME: {
                'handlers': ['gelf'],
                'level': 'DEBUG',
            },
            'django.request': {
                'handlers': ['gelf'],
                'level': 'WARNING',
                'propagate': False,
            },
        },
    }
