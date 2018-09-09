from django.db import migrations
from nalkinscloud_mosquitto.models import DeviceType, DeviceModel, Devices, AccessList


def create_device_types(apps, schema_editor):
    device_type_list = ['dht', 'switch', 'magnet', 'distillery', 'service', 'user']
    for type_name in device_type_list:
        if type_name is not None:
            DeviceType.objects.create_device_type(type_name=type_name)


def create_device_models(apps, schema_editor):
    device_model_list = ['esp8266', 'service', 'application']
    for model_name in device_model_list:
        if model_name is not None:
            DeviceModel.objects.create_device_model(model_name=model_name)


def create_devices(apps, schema_editor):
    devices_list = [{'device_id': 'test_switch_simulator',
                     'password': 'nalkinscloud',
                     'model': 'esp8266',
                     'type': 'switch'},
                    {'device_id': 'test_dht_simulator',
                     'password': 'nalkinscloud',
                     'model': 'esp8266',
                     'type': 'dht'}]
    for device in devices_list:
        Devices.objects.create(device_id=device['device_id'],
                               password=device['password'],
                               model=DeviceModel.objects.get(model=device['model']),
                               type=DeviceType.objects.get(type=device['type']),
                               is_enabled=1)


def create_acls(apps, schema_editor):
    acl_list = [{'device': 'test_switch_simulator',
                 'topic': 'test_topic'},
                {'device': 'test_dht_simulator',
                 'topic': 'test_topic'}]
    for acl in acl_list:
        AccessList.objects.create(device=Devices.objects.get(device_id=acl['device']),
                                  topic=acl['topic'],
                                  rw=2,
                                  is_enabled=1)


class Migration(migrations.Migration):

    dependencies = [
        ('nalkinscloud_mosquitto', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_device_types),
        migrations.RunPython(create_device_models),
        migrations.RunPython(create_devices),
        migrations.RunPython(create_acls),
    ]
