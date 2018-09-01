from django.test import TestCase, SimpleTestCase
from django.test.client import RequestFactory

from django_user_email_extension.models import User
from nalkinscloud_api.functions import *


class TestNalkinscloudApiFunctions(TestCase):

    def test_build_json_response(self):
        values = build_json_response('some value', 'some message')
        self.assertEqual(values, {
            'status': 'some value',
            'message': 'some message'
        })

    def test_build_json_response_2(self):
        values = build_json_response('some value', 'some message')
        self.assertNotEqual(values, {
            'status': '',
            'message': ''
        })

    def test_build_json_response_4(self):
        values = build_json_response(1, 'some message')
        self.assertEqual(values, False)
    
    def test_build_json_response_5(self):
        values = build_json_response(1, 'some message')
        self.assertNotEqual(values, {
            'status': 'some value',
            'message': 'some message'
        })

'''
class SimpleTest(TestCase):
    def setUp(self):
        User.objects.create(email='alice@gmail.com', password='12345678')

    def test_secure_page(self):
        self.client.login(email='alice@gmail.com', password='12345678')
        response = self.client.get('/manufacturers/', follow=True)
        User.objects.get(email='alice@gmail.com')
        self.assertEqual(response.context['email'], 'temporary@gmail.com')


class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(email="alice", password="12345678")
        User.objects.create(email="bob@gmail.com", password="")
        User.objects.create(email="alice@gmail.com", password="12345678")
        User.objects.create(email="alice@fullname.com",
                            password="12345678",
                            first_name='alice',
                            last_name='alice')

    def test_animals_can_speak(self):
        """Animals that can speak are correctly identified"""
        a = User.objects.get(email="alice")
        b = User.objects.get(email="bob@gmail.com")
        c= User.objects.get(email="alice@fullname.com")
        self.assertEqual(a.get_full_name(), '')
        self.assertEqual(b.get_full_name(), '')
        self.assertEqual(c.get_full_name(), 'alice alice')
'''
