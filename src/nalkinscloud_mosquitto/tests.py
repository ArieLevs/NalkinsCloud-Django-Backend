from django.test import TestCase
from nalkinscloud_mosquitto.functions import *


class TestBrokerFunctions(TestCase):
    def setUp(self):
        self.username = 'some_username'
        self.email = 'test@nalkins.cloud'
        self.password = 'nalkinscloud'

        self.user = User.objects.create_user(email=self.email, password=self.password,
                                             user_name=self.username)

        self.device_id = 'some_device_id'
        self.device_password = 'nalkinscloud'
        self.device_model = 'application'
        self.device_type = 'user'

        self.device = Device.objects.create_device(device_id=self.device_id, password=self.device_password,
                                                   model=DeviceModel.objects.get(model=self.device_model),
                                                   type=DeviceType.objects.get(type=self.device_type))

        # Add above device, to above user
        self.device_name = 'test_device_name'
        self.customer_device = CustomerDevice.objects.create(user_id=self.user, device_id=self.device,
                                                             device_name=self.device_name)

        self.topic = 'some/important/topic'
        # Generate access list record
        # AccessList.objects.get_or_create(device_id=self.device_id, topic=self.topic)

    def test_is_device_id_exists(self):
        self.assertTrue(is_device_id_exists(self.device_id))
        self.assertFalse(is_device_id_exists('non_existing_device_id'))

    def test_update_device_pass(self):
        self.assertTrue(update_device_pass(self.device_id, 'new_password'))
        self.assertFalse(update_device_pass('non_existing_device_id', 'new_password'))

    def test_insert_into_access_list(self):
        self.assertFalse(AccessList.objects.filter(device_id=self.device_id, topic='some/other/topic').exists())
        insert_into_access_list(device=self.device, topic='some/other/topic')
        self.assertTrue(AccessList.objects.filter(device_id=self.device_id, topic='some/other/topic').exists())

    def test_is_device_owned_by_user(self):
        self.assertTrue(is_device_owned_by_user(device=self.device, user=self.user))
        CustomerDevice.objects.filter(user_id=self.user, device_id=self.device).delete()
        self.assertFalse(is_device_owned_by_user(device=self.device, user=self.user),
                         "Should return False since current user does not have any devices")
        # Add current user, current device
        CustomerDevice.objects.create(user_id=self.user, device_id=self.device)

    def test_device_has_any_owner(self):
        self.assertTrue(device_has_any_owner(device=self.device))

        device = Device.objects.create_device(device_id='test_owner_device_id', password=self.device_password,
                                              model=DeviceModel.objects.get(model=self.device_model),
                                              type=DeviceType.objects.get(type=self.device_type))
        self.assertFalse(device_has_any_owner(device=device))

    def test_insert_into_customer_devices(self):
        self.assertFalse(insert_into_customer_devices(user=self.user,
                                                      device=self.device,
                                                      device_name=self.device_name),
                         "Should return False since already exists")
        CustomerDevice.objects.filter(user_id=self.user, device_id=self.device).delete()
        self.assertTrue(insert_into_customer_devices(user=self.user,
                                                     device=self.device,
                                                     device_name=self.device_name))
        CustomerDevice.objects.filter(user_id=self.user, device_id=self.device).delete()

    def test_remove_from_customer_devices(self):
        self.assertTrue(remove_from_customer_devices(user=self.user, device=self.device))
        self.assertFalse(remove_from_customer_devices(user=self.user, device=self.device))
        # Return CustomerDevice deleted in this test
        CustomerDevice.objects.create(user_id=self.user, device_id=self.device)

    def test_remove_from_access_list(self):
        AccessList.objects.create(device_id=self.device_id, topic='some/remove_acl_test/topic')
        self.assertTrue(AccessList.objects.filter(device_id=self.device_id,
                                                  topic='some/remove_acl_test/topic').exists())
        remove_from_access_list(device_id=self.device_id, topic='some/remove_acl_test/topic')
        self.assertFalse(AccessList.objects.filter(device_id=self.device_id,
                                                   topic='some/remove_acl_test/topic').exists())

    def test_get_customers_devices(self):
        self.assertEqual(get_customers_devices(self.user).count(), 1,
                         "Should return 1, as current user has one device")

        # Generate another device
        device = Device.objects.create_device(device_id='some_device_id_2', password=self.device_password,
                                              model=DeviceModel.objects.get(model=self.device_model),
                                              type=DeviceType.objects.get(type=self.device_type))

        # Add just created device to test user
        customer_device = CustomerDevice.objects.create(user_id=self.user, device_id=device)
        customer_device.device_name = 'test_device_name_2'
        customer_device.save()

        self.assertEqual(get_customers_devices(self.user).count(), 2,
                         "Should return 2, as another device added to current user")

        customer_devices = get_customers_devices(self.user)
        # For each device found for current user
        for customer_device in customer_devices:
            # Make sure the device found is one of the two devices of the user
            self.assertIn(customer_device.device_name, [self.device_name, customer_device.device_name],
                          "Should be equal to both device names of the user")

    def test_insert_new_client_to_devices(self):
        # Current devices of type 'user' should be 1
        self.assertEqual(Device.objects.filter(type=DeviceType.objects.get(type='user')).count(), 1,
                         "Should have only 1 device of type 'user'")
        self.assertTrue(insert_new_client_to_devices(email='test2@nalkins.cloud',
                                                     password=self.device_password,
                                                     ip='127.0.0.1'))
        self.assertEqual(Device.objects.filter(type=DeviceType.objects.get(type='user')).count(), 2,
                         "Should have 2 devices of type 'user'")
        self.assertFalse(insert_new_client_to_devices(email='test2@nalkins.cloud',
                                                      password=self.device_password,
                                                      ip='127.0.0.1'),
                         "Should return False since device already exists")

    def test_get_device_name_by_id(self):
        self.assertEqual(get_device_name_by_id(self.device), self.device_name)
