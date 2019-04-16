
from django.utils.crypto import get_random_string
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import AccessToken
from rest_framework.test import APITestCase
from nalkinscloud_api.functions import *
import datetime
import logging
from nalkinscloud_django.settings import PROJECT_NAME

# Define logger
logger = logging.getLogger(PROJECT_NAME)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)


class TestFunctions(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@nalkins.cloud', password='12345678',
                                             user_name='some_username')
        self.oauth_client = Application.objects.create(client_id='some_client_id', client_secret='some_client_secret')

    def test_build_json_response(self):
        values = build_json_response('some value', 'some message')
        self.assertEqual(values, {
            'status': 'some value',
            'message': 'some message'
        })
        self.assertNotEqual(values, {
            'status': '',
            'message': ''
        })
        values = build_json_response(1, ['array_value'])
        self.assertEqual(values, {
            'status': 1,
            'message': ['array_value']
        })

    def test_get_utc_datetime(self):
        date_time = datetime.datetime.strptime('2019-01-01 12:01:01', '%Y-%m-%d %H:%M:%S')
        none_type = None

        self.assertFalse(get_utc_datetime(none_type))
        self.assertEqual('2019-01-01 12:01:01+00:00', str(get_utc_datetime(date_time)))

    def test_is_username_exists(self):
        self.assertTrue(is_username_exists(username='some_username'))
        self.assertFalse(is_username_exists(username='some_other_username'))

    def test_is_email_exists(self):
        self.assertTrue(is_email_exists(email='test@nalkins.cloud'))
        self.assertFalse(is_email_exists(email='test2@nalkins.cloud'))

    def test_is_client_secret_exists(self):
        self.assertTrue(is_client_secret_exists(client_secret='some_client_secret'))
        self.assertFalse(is_client_secret_exists(client_secret='some_other_client_secret'))


class RegistrationAPIViewTestCase(APITestCase):
    def setUp(self):
        # Create OAuth application
        self.oauth_client_id = 'some_client_id'
        self.oauth_client_secret = 'some_client_secret'

        self.oauth_client = Application.objects.create(client_id=self.oauth_client_id,
                                                       client_secret=self.oauth_client_secret)

        self.email = "test@nalkins.cloud"
        self.password = "nalkinscloud"

        # Generate basic test user
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            is_active=True
        )

        # Generate access token (oauth) for test user
        expires = timezone.now() + datetime.timedelta(seconds=36000)
        self.access_token = AccessToken.objects.create(
            user=self.user,
            application=self.oauth_client,
            scope='',
            token=get_random_string(length=32),
            expires=expires)
        self.access_token.save()

        self.health_check_url = reverse('health_check')
        self.registration_url = reverse('register')

    def test_registration(self):
        """
        Test Registration view
        """
        logger.debug("executing test_registration")
        post_body = {
            'client_secret': self.oauth_client_secret,
            'email': 'arielev@nalkins.cloud',
            'password': self.password,
            'first_name': 'Arie',
            'last_name': 'Lev'
        }
        response = self.client.post(self.registration_url, data=post_body, format='json')
        logger.debug("test_registration response: " + str(response.json()))
        self.assertEqual(201, response.status_code, "Should register new user successfully")

        self.assertEqual(User.objects.count(), 2, "Two users should be present in the system by this point")

    def test_health_check_view(self):
        """
        Test Health Check view
        :return:
        """
        # Set current client with a token fot authentication
        logger.debug("executing test_health_check_view with token: " + str(self.access_token))
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token))

        response = self.client.post(self.health_check_url)
        logger.debug('test_health_check_view response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return username")
