
from django.test import TestCase
from nalkinscloud_api.functions import *
import datetime
from datetime import timedelta
import pytz


class TestFunctions(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='test@nalkins.cloud', password='12345678')

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

    def test_is_email_exists(self):
        self.assertTrue(is_email_exists(email='test@nalkins.cloud'))
        self.assertFalse(is_email_exists(email='test2@nalkins.cloud'))
