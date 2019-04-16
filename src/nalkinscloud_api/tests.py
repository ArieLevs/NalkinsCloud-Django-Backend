
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


class TestFunctions(TestCase):

    def setUp(self):
        self.oauth_client_id = 'some_client_id'
        self.oauth_client_secret = 'some_client_secret'

        self.oauth_client = Application.objects.create(client_id=self.oauth_client_id,
                                                       client_secret=self.oauth_client_secret)

        self.username = 'some_username'
        self.email = "test@nalkins.cloud"
        self.password = "nalkinscloud"

        self.user = User.objects.create_user(email=self.email, password=self.password,
                                             user_name=self.username)

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
        self.assertTrue(is_username_exists(username=self.username))
        self.assertFalse(is_username_exists(username='some_other_username'))

    def test_is_email_exists(self):
        self.assertTrue(is_email_exists(email=self.email))
        self.assertFalse(is_email_exists(email='test2@nalkins.cloud'))

    def test_is_client_secret_exists(self):
        self.assertTrue(is_client_secret_exists(client_secret=self.oauth_client_secret))
        self.assertFalse(is_client_secret_exists(client_secret='some_other_client_secret'))


class APIViewsTestCase(APITestCase):
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
        self.device_list_url = reverse('device_list')

    def test_registration(self):
        """
        Test Registration view
        """
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

        # Peform same registration process again
        response = self.client.post(self.registration_url, data=post_body, format='json')
        self.assertEqual(409, response.status_code, "Should return 409 conflict, email already exists")

        # Change client_secret to non valid value
        post_body['client_secret'] = 'some_non_existing_client_id'
        response = self.client.post(self.registration_url, data=post_body, format='json')
        self.assertEqual(401, response.status_code, "Should return not authorized")

        self.assertEqual(User.objects.count(), 2, "Two users should be present in the system by this point")

    def test_health_check_view(self):
        """
        Test Health Check view
        :return:
        """
        # Set current client with a token fot authentication
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token))

        response = self.client.post(self.health_check_url)
        logger.debug('test_health_check_view response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return username")

    def test_device_list_view(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token))
        response = self.client.post(self.device_list_url)
        logger.debug('test_device_list_view response: ' + str(response.json()))
        self.assertEqual(204, response.status_code, "Should return empty list")
