
from django.test import TestCase
from nalkinscloud_api.functions import *
import datetime


class TestAPIFunctions(TestCase):
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
