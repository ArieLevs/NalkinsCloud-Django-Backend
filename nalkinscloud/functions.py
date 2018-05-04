# For reading outsource file output
from django.contrib.auth.hashers import make_password

from nalkinscloud.models import User
from django.conf import settings
import MySQLdb

# For password generating
import random
import string
import os

from pytz import utc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DjangoDB(object):
    _db_connection = None
    _db_cur = None

    def __init__(self):
        self._db_connection = MySQLdb.connect(settings.DATABASES['default']['HOST'],
                                              settings.DATABASES['default']['USER'],
                                              settings.DATABASES['default']['PASSWORD'],
                                              'django')
        self._db_cur = self._db_connection.cursor()

    def query(self, query, params):
        self._db_cur.execute(query, params)
        return self._db_cur.fetchall()

    def commit(self):
        self._db_connection.commit()

    def __del__(self):
        self._db_connection.close()


# Build a json format and return
def build_json_response(status, value):
    return {
        'status': status,
        'message': value
    }


def generate_user_name(first_name, last_name):
    user_name = first_name + '.' + last_name + '.'
    return user_name.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))


def generate_random_pass():
    # Generates password (8 characters long mixed digits with letters)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def generate_random_16_digit_string():
    # Generate random string (16 characters long mixed digits with letters)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))


# Get the generated password as PBKDF2 hash,
# using the 'generatePBKDF2pass'
'''def hash_password_old(password):
    py2output = subprocess.check_output([os.path.join(BASE_DIR, 'scripts/generatePBKDF2pass'), '-p', str(password)])
    hashed_pass = py2output.decode('utf-8')
    # Remove '\n' from the generated pass
    return hashed_pass.replace('\n', '')
    '''


def hash_password(password):
    return make_password(password, salt=None, hasher='pbkdf2_sha256')


# Function receive datetime object, and return an datetime object with GMT+0 (UTC time)
def get_utc_datetime(local_date):
    # utc = pytz.utc
    return local_date.astimezone(utc)


def is_username_exists(username):
    return User.objects.filter(user_name=username).exists()


def is_email_exists(email):
    return User.objects.filter(email=email).exists()
