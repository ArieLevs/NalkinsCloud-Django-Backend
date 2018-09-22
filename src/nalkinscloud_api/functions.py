
from django.contrib.auth.hashers import make_password

from django_user_email_extension.models import User
from oauth2_provider.models import Application

# For password generating
import random
import string

from pytz import utc
import datetime


def build_json_response(status, value):
    """
    Generate json format from input params

    :param status: string
    :param value: string
    :return: json array
    """
    return {
        'status': status,
        'message': value
    }


def generate_user_name(first_name, last_name):
    """
    Generate username using first_name, last_name and random create stings, for example:
    params of: 'john', 'smith'
    return of: john.smith.QJZV4RWL

    :param first_name: string users first name
    :param last_name: string users last name
    :return: string Random generated username
    """
    return first_name + '.' + last_name + '.' + generate_random_8_char_string()


def generate_random_8_char_string():
    """
    Generate random 8 characters string

    :return: string
    """
    # Generates password (8 characters long mixed digits with letters)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def generate_random_16_char_string():
    """
    Generate random 16 characters string

    :return: string
    """
    # Generate random string (16 characters long mixed digits with letters)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))


def hash_pbkdf2_sha256_password(password):
    """
    Hash input password using pbkdf2_sha256 algorithm, for example
    params of: 12345678
    return of: pbkdf2_sha256$100000$Svjk1keU9azH$pxoHBlU4LkAItt6Y5gkeAB1gIrFOePjOxiKozh6zhSI=

    :param password: string
    :return: hashed password
    """
    return make_password(password, salt=None, hasher='pbkdf2_sha256')


def get_utc_datetime(local_date):
    """
    Receive datetime object, and return an datetime object with GMT+0 (UTC time)

    :param local_date: pytz.utc
    :return: pytz.utc, or False if local_date is not datetime
    """
    if isinstance(local_date, datetime.datetime):
        # utc = pytz.utc
        return local_date.astimezone(utc)
    else:
        return False


def is_username_exists(username):
    """
    Check if username exist in 'User' model

    :param username: string
    :return: True if user exists, else False
    """
    return User.objects.filter(user_name=username).exists()


def is_email_exists(email):
    """
    Check if email exist in 'User' model

    :param email: string
    :return: True if email exists, else False
    """
    return User.objects.filter(email=email).exists()


def is_client_secret_exists(client_secret):
    """
    Check if client_secret exist in 'Application' model (oauth2_provider)

    :param client_secret:
    :return: True if client_secret exists
    """
    return Application.objects.filter(client_secret=client_secret).exists()
