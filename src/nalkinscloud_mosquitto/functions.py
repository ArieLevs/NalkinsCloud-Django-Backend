
from nalkinscloud_mosquitto.models import *


def update_device_pass(device_id, password):
    """
    Update input password of Device with 'device_id'
    Return True on success, False if Device with device_id does not exist

    :param device_id: string device id
    :param password: string password
    :return: boolean
    """
    try:
        device = Device.objects.get(device_id=device_id)
        device.set_password(password)
        device.save()
        return True
    except Device.DoesNotExist:
        return False


def insert_into_access_list(device, topic):
    """
    Add new record to 'access_list' table with input Device and a topic

    :param device: Device instance
    :param topic: string
    :return: None
    """
    new_access_list, created = AccessList.objects.get_or_create(device=device, topic=topic)
    if created:  # We are adding a new device from a customer
        new_access_list.rw = 2
        new_access_list.save()
    else:  # Just update the access list
        new_access_list.save()


def is_device_id_exists(device_id):
    """
    Return True Device object if exists, else False

    :param device_id: string device_id
    :return: boolean
    """
    return Device.objects.filter(device_id=device_id).exists()


def is_device_owned_by_user(device, user):
    """
    Returns True if input user, is one of the input device owner (record exists) else return False

    :param device: Device instance
    :param user: User instance
    :return: boolean
    """
    devices = CustomerDevice.objects.filter(device_id=device)  # For each device can be 0 or many owners
    if devices.exists():  # If found a device then there might be a match
        for device in devices:
            if device.user_id == user:  # If user, and the device found math
                return True
    return False


def device_has_any_owner(device):
    """
    Return True if device has an owner (record exists)

    :param device: Device instance
    :return: boolean
    """
    devices = CustomerDevice.objects.filter(device_id=device)
    if devices.exists():
        return True
    return False


def insert_into_customer_devices(user, device, device_name, owner=False):
    """
    Create new customer device,
    if owner is True, then model will also set current
    Create a new owner for a device (create new record),
    Return True if new CustomerDevice instance created, else return False

    :param user: User instance
    :param device: Device instance
    :param device_name: string
    :param owner: boolean
    :return: boolean
    """
    new_customer_device, created = CustomerDevice.objects.get_or_create(user_id=user, device_id=device,
                                                                        device_name=device_name, is_owner=owner)
    if created:
        new_customer_device.save()
        return True
    return False  # The device already exists in the DB


def remove_from_customer_devices(user, device):
    """
    Remove CustomerDevice instance with for given User and Device instances,
    delete() function return num of rows deleted, and instance types
    if the num of rows deleted is 0, return False, else return True

    :param user: User instance
    :param device: Device instance
    :return: boolean
    """
    if CustomerDevice.objects.filter(user_id=user, device_id=device).delete()[0] == 0:
        return False
    return True


def remove_from_access_list(device_id, topic):
    """
    Remove AccessList instance with for given device_id and topic,
    delete() function return num of rows deleted, and instance types
    if the num of rows deleted is 0, return False, else return True

    :param device_id: string
    :param topic: string
    :return: boole
    """
    device_obj = Device.objects.get(device_id=device_id)
    if AccessList.objects.filter(device=device_obj, topic=topic).delete()[0] == 0:
        return False
    return True


def get_customers_devices(user):
    """
    Return a list of CustomerDevices instances, that have the User instance in their PK
    :param user: User instance
    :return: list of CustomerDevice instances
    """
    return CustomerDevice.objects.filter(user_id=user)


def insert_new_client_to_devices(email, password, ip):
    """
    Create a new Device instance record, of type 'user' and model 'application',
    With its device_id field as the users email.
    This is needed since a user (some client) is also a device, that will need to connect to the broker
    Return True if new Device instance created, else return False

    :param email: string
    :param password: string
    :param ip: string
    :return: boolean
    """
    new_device, created = Device.objects.get_or_create(device_id=email,
                                                       model=DeviceModel.objects.get(model='application'),
                                                       type=DeviceType.objects.get(type='user'))
    if created:
        new_device.password = password
        new_device.is_enabled = 1
        new_device.last_connection_ip = ip
        new_device.save()
        return True
    return False  # The device already exists in the DB


def get_device_name_by_id(device):
    """
    Return devices name as a string, by a giver Device instance

    :param device: Device instance
    :return: string
    """
    return CustomerDevice.objects.get(device_id=device).device_name
