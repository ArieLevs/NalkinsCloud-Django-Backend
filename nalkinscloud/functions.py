# For reading outsource file output
import subprocess
from django.contrib.auth.hashers import make_password

# For password generating
import random
import string
import os

from pytz import utc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Build a json format and return
def build_json_response(status, value):
    response = {
        'status': status,
        'message': value
    }
    return response


def generate_random_pass():
    # Generates password (8 characters long mixed digits with letters)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def generate_random_16_digit_string():
    # Generate random string (16 characters long mixed digits with letters)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))


# Get the generated password as PBKDF2 hash,
# using the 'generatePBKDF2pass'
def hash_password(password):
    py2output = subprocess.check_output([os.path.join(BASE_DIR, 'scripts/generatePBKDF2pass'), '-p', str(password)])
    hashed_pass = py2output.decode('utf-8')
    # Remove '\n' from the generated pass
    return hashed_pass.replace('\n', '')


def hash_password1(password):
    return make_password(password, salt=None, hasher='pbkdf2_sha256')


# Function receive datetime object, and return an datetime object with GMT+0 (UTC time)
def get_utc_datetime(local_date):
    # utc = pytz.utc
    return local_date.astimezone(utc)
