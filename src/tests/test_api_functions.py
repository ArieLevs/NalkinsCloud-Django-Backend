
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APITestCase
from oauth2_provider.models import AccessToken
from oauth2_provider.models import Application

from nalkinscloud_mosquitto.models import Device, DeviceType, DeviceModel, CustomerDevice
from django_user_email_extension.models import User
import datetime
import logging
from nalkinscloud_django.settings import PROJECT_NAME

# Define logger
logger = logging.getLogger(PROJECT_NAME)


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

        # Generate test device
        self.device_id = 'api_test_device_id'
        self.device_password = 'nalkinscloud'
        self.device_model = 'esp8266'
        self.device_type = 'dht'

        self.device = Device.objects.create_device(device_id=self.device_id, password=self.device_password,
                                                   model=DeviceModel.objects.get(model=self.device_model),
                                                   type=DeviceType.objects.get(type=self.device_type))

        # Generate users device
        self.user_device_id = self.user.email
        self.user_device_model = 'application'
        self.user_device_type = 'user'

        self.user_device = Device.objects.create_device(device_id=self.user_device_id, password=self.device_password,
                                                        model=DeviceModel.objects.get(model=self.user_device_model),
                                                        type=DeviceType.objects.get(type=self.user_device_type))

        # Set current client with a token fot authentication
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.access_token))

        self.health_check_url = reverse('health_check')
        self.registration_url = reverse('register')
        self.device_activation_url = reverse('device_activation')
        self.device_list_url = reverse('device_list')
        self.forgot_password_url = reverse('forgot_password')
        self.get_device_pass_url = reverse('get_device_pass')
        self.remove_device_url = reverse('remove_device')
        self.reset_password_url = reverse('reset_password')
        self.update_device_pass_url = reverse('update_device_pass')

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
        self.assertEqual(201, response.status_code, "Should return 201, register new user successfully")

        # Perform same registration process again
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
        response = self.client.post(self.health_check_url)
        logger.debug('test_health_check_view response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return username")

    def test_device_activation_view_204(self):
        """
        Test case when trying to attach a device that does not exists
        :return:
        """
        post_body = {
            'device_id': 'non_existing_device',
            'device_name': 'device_activation_test'
        }
        response = self.client.post(self.device_activation_url, data=post_body)
        self.assertEqual(204, response.status_code, "Should return 204 since device does not exists")

    def test_device_activation_view_400_1(self):
        """
        Test case when calling the api with no data
        :return:
        """
        response = self.client.post(self.device_activation_url)
        logger.debug('test_device_activation_view_400_1 response: ' + str(response.json()))
        self.assertEqual(400, response.status_code, "Should return error 400 since there are missing values")

    def test_device_activation_view_400_2(self):
        """
        Test case when one of data parameters empty
        :return:
        """
        post_body = {
            'device_id': '',
            'device_name': 'device_activation_test'
        }
        response = self.client.post(self.device_activation_url, data=post_body)
        logger.debug('test_device_activation_view_400_2 response: ' + str(response.json()))
        self.assertEqual(400, response.status_code, "Should return 400 since 'device_id' is blank")
        self.assertEqual(response.json(), {'device_id': ['This field may not be blank.']},
                         "Should return blank field not allowed")

    def test_device_activation_view_409(self):
        """
        Test case when a device has an owner and its not the current user
        :return:
        """
        # Generate another test user
        user = User.objects.create_user(
            email='device@activate.test',
            password=self.password,
            is_active=True
        )
        # Generate another test device
        device = Device.objects.create_device(device_id='device_activation_test_id', password=self.device_password,
                                              model=DeviceModel.objects.get(model=self.device_model),
                                              type=DeviceType.objects.get(type=self.device_type))
        # Attach just created user and device
        CustomerDevice.objects.create(user_id=user, device_id=device)

        # Test attaching other users device to current user
        post_body = {
            'device_id': device,
            'device_name': 'device_activation_test'
        }
        response = self.client.post(self.device_activation_url, data=post_body)
        logger.debug('test_device_activation_view_409 response: ' + str(response.json()))
        self.assertEqual(409, response.status_code, "Should return 409 conflict, device owned by other user")

    def test_device_activation_view_200_1(self):
        """
        Test case when all is OK and an non owned device attached to current user
        :return:
        """
        post_body = {
            'device_id': self.device_id,
            'device_name': 'device_activation_test'
        }
        response = self.client.post(self.device_activation_url, data=post_body)
        logger.debug('test_device_activation_view_200_1 response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return 200, device attached")

    def test_device_activation_view_200_2(self):
        """
        Test case when trying to attach a device that is already attached
        :return:
        """

        CustomerDevice.objects.create(user_id=self.user, device_id=self.device)
        post_body = {
            'device_id': self.device_id,
            'device_name': 'test_device_activation_view_200_2'
        }
        response = self.client.post(self.device_activation_url, data=post_body)
        logger.debug('test_device_activation_view_200_2 response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return 200, device already attached to current user")
        CustomerDevice.objects.filter(user_id=self.user, device_id=self.user_device).delete()

    def test_device_list_view_204(self):
        """
        Test case that should return an empty device list
        :return:
        """
        response = self.client.post(self.device_list_url)
        self.assertEqual(204, response.status_code, "Should return empty list")

    def test_device_list_view_200(self):
        """
        Test case that should return at least 1 length device list
        :return:
        """
        CustomerDevice.objects.create(user_id=self.user, device_id=self.device)
        response = self.client.post(self.device_list_url)
        logger.debug('test_device_list_view_200 response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return devices list")
        CustomerDevice.objects.filter(user_id=self.user, device_id=self.user_device).delete()

    def test_forgot_password_view_400(self):
        """
        Test case when no data provided
        :return:
        """
        response = self.client.post(self.forgot_password_url)
        logger.debug('test_forgot_password_view_400 response: ' + str(response.json()))
        self.assertEqual(400, response.status_code, "Should return 400, since missing data")

    def test_forgot_password_view_401(self):
        """
        Test case when wrong client secret used
        :return:
        """
        post_data = {
            'client_secret': 'some_non_valid_client_secret',
            'email': self.user.email
        }
        response = self.client.post(self.forgot_password_url, data=post_data)
        logger.debug('test_forgot_password_view_401 response: ' + str(response.json()))
        self.assertEqual(401, response.status_code, "Should return 401, since client secret not exists")

    def test_forgot_password_view_200_1(self):
        """
        Test case when non existing email requested forgot password
        :return:
        """
        post_body = {
            'client_secret': self.oauth_client_secret,
            'email': 'some@not_existing.email',
        }
        response = self.client.post(self.forgot_password_url, data=post_body, format='json')
        self.assertEqual(200, response.status_code, "Should return 200, although email does not exists")

    def test_forgot_password_view_200_2(self):
        """
        Test case when process should pass successfully
        :return:
        """
        post_data = {
            'client_secret': self.oauth_client_secret,
            'email': self.user.email,
        }
        response = self.client.post(self.forgot_password_url, data=post_data, format='json')
        logger.debug('test_forgot_password_view_200_2 response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return 200, process completed")

    def test_get_device_pass_view_400(self):
        """
        Test case when no data received
        :return:
        """
        response = self.client.post(self.get_device_pass_url)
        logger.debug('test_get_device_pass_view_400 response: ' + str(response.json()))
        self.assertEqual(400, response.status_code, "Should return 400, since missing data")

    def test_get_device_pass_view_204(self):
        """
        Test case when non existing device id received
        :return:
        """
        post_data = {
            'device_id': 'some_non_existing_device_id'
        }
        response = self.client.post(self.get_device_pass_url, data=post_data)
        self.assertEqual(204, response.status_code, "Should return 204, since device id does not exists")

    def test_get_device_pass_view_409(self):
        """
        Test case when trying to update password for a device that's owned by another user
        :return:
        """
        # Generate another test user
        user = User.objects.create_user(
            email='device@get_pass.test',
            password=self.password,
            is_active=True
        )
        # Generate another test device
        device = Device.objects.create_device(device_id='get_device_pass_test_id', password=self.device_password,
                                              model=DeviceModel.objects.get(model=self.device_model),
                                              type=DeviceType.objects.get(type=self.device_type))
        # Attach just created user and device
        CustomerDevice.objects.create(user_id=user, device_id=device)

        post_data = {
            'device_id': device.device_id
        }
        response = self.client.post(self.get_device_pass_url, data=post_data)
        self.assertEqual(409, response.status_code, "Should return 409, since device belongs to another user")

    def test_get_device_pass_view_200(self):
        """
        Test case when process should pass successfully
        :return:
        """
        CustomerDevice.objects.create(user_id=self.user, device_id=self.device)
        post_data = {
            'device_id': self.device.device_id
        }
        response = self.client.post(self.get_device_pass_url, data=post_data)
        self.assertEqual(200, response.status_code, "Should return 200, process succeeded")

    def test_remove_device_view_400(self):
        """
        Test case when no data received
        :return:
        """
        response = self.client.post(self.remove_device_url)
        logger.debug('test_remove_device_view_400 response: ' + str(response.json()))
        self.assertEqual(400, response.status_code, "Should return 400, since missing data")

    def test_remove_device_view_409_200(self):
        """
        Test case when no data received
        :return:
        """
        # Generate another test device
        device = Device.objects.create_device(device_id='remove_device_test_id', password=self.device_password,
                                              model=DeviceModel.objects.get(model=self.device_model),
                                              type=DeviceType.objects.get(type=self.device_type))

        post_data = {
            'device_id': device.device_id
        }
        response = self.client.post(self.remove_device_url, data=post_data)
        logger.debug('test_remove_device_view_409_200 response: ' + str(response.json()))
        self.assertEqual(409, response.status_code, "Should return 409, since device is not owned by current user")

        # Attach just created device to current user
        CustomerDevice.objects.create(user_id=self.user, device_id=device)

        response = self.client.post(self.remove_device_url, data=post_data)
        logger.debug('test_remove_device_view_409_200 response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return 200, since device owned by current user")

    def test_reset_password_view_400(self):
        """
        Test case when no data received
        :return:
        """
        post_data = {
            'current_password': '',
            'new_password': self.password
        }
        response = self.client.post(self.reset_password_url, data=post_data)
        logger.debug('test_reset_password_view_400 response: ' + str(response.json()))
        self.assertEqual(400, response.status_code, "Should return 400, since missing data")

    def test_reset_password_view_422(self):
        """
        Test case when wrong incorrect password received
        :return:
        """
        post_data = {
            'current_password': 'somE_RandOm_PassWorD',
            'new_password': self.password
        }
        response = self.client.post(self.reset_password_url, data=post_data)
        logger.debug('test_reset_password_view_422 response: ' + str(response.json()))
        self.assertEqual(422, response.status_code, "Should return 422, since current password is incorrect")

    def test_reset_password_view_200(self):
        """
        Test case when wrong correct password received
        :return:
        """
        post_data = {
            'current_password': self.password,
            'new_password': self.password
        }
        response = self.client.post(self.reset_password_url, data=post_data)
        logger.debug('test_reset_password_view_200 response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return 200, since current password is correct")

    def test_update_mqtt_user_pass_view_200(self):
        """
        Test case when pass updates successfully
        :return:
        """
        response = self.client.post(self.update_device_pass_url)
        logger.debug('test_update_mqtt_user_pass_view_200 response: ' + str(response.json()))
        self.assertEqual(200, response.status_code, "Should return 200")
