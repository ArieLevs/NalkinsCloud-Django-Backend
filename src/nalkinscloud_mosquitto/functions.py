
from nalkinscloud_mosquitto.models import *


# Update device password on mosquitto DB
def update_device_pass_mosquitto_db(device_id, password):
    try:
        device = Device.objects.get(device_id=device_id)
        device.set_password(password)
        device.save()
        return True
    except Device.DoesNotExist:
        return False


def insert_into_acls_mosquitto_db(device_id, topic):
    new_access_list, created = AccessList.objects.get_or_create(device_id=device_id, topic=topic)
    if created:  # We are adding a new device from a customer
        new_access_list.rw = 2
        new_access_list.save()
    else:  # Just update the access list
        new_access_list.save()


# Get client ID from mosquitto if exists
def is_device_id_exists(device_id):
    return Device.objects.filter(device_id=device_id).exists()


# Get current owner id of the device
def get_device_owner(device_id, logged_in_user_id):
    user_id_by_device = CustomerDevice.objects.filter(device_id=device_id)  # Get users id by device id
    if user_id_by_device:  # If found a device with that device id then there might be a match
        for owner in user_id_by_device:
            if str(owner.user_id) == logged_in_user_id:  # If logged in user, and the device found math
                return True
    return False


def insert_into_customer_devices(user_id, device_id, device_name):
    new_customer_device, created = CustomerDevice.objects.get_or_create(user_id=user_id, device_id=device_id)
    if created:  # We are adding a new device from a customer
        new_customer_device.device_name = device_name
        new_customer_device.save()
        return True
    return False  # The device already exists in the DB


def remove_from_customer_devices(user_id, device_id):
    CustomerDevice.objects.filter(user_id=user_id, device_id=device_id).delete()


def remove_from_acls(device_id, topic):
    device_obj = Device.objects.get(device_id=device_id)
    AccessList.objects.filter(device=device_obj, topic=topic).delete()


# Get customers devices by using user id
def get_customers_devices(user_id):
    return CustomerDevice.objects.filter(user_id=user_id)


# Add new device to the devices table
def insert_new_client_to_devices(email, password, ip):
    new_device, created = Device.objects.get_or_create(device_id=email,
                                                       model=DeviceModel.objects.get(model='application'),
                                                       type=DeviceType.objects.get(type='user'))
    if created:  # We are adding a new device
        new_device.password = password
        new_device.is_enabled = 1
        new_device.last_connection_ip = ip
        new_device.save()
        return True
    return False  # The device already exists in the DB


def get_device_name_by_id(device_id):
    return CustomerDevice.objects.filter(device_id=device_id).device_name
