from django.db import migrations
from nalkinscloud_mosquitto.models import DeviceType, DeviceModel


def create_device_types(apps, schema_editor):
    device_type = DeviceType.objects.create()
    device_type_list = ['dht', 'switch', 'magnet', 'distillery', 'service', 'user',]
    for type_name in device_type_list:
        if type_name is not None:
            print('#' + type_name + '#')
            device_type.type = type_name
            device_type.save()


def create_device_models(apps, schema_editor):
    device_model = DeviceModel.objects.create()
    device_model_list = ['esp8266', 'service', 'application',]
    for model_name in device_model_list:
        if model_name is not None:
            print('#' + model_name + '#')
            device_model.type = model_name
            device_model.save()


class Migration(migrations.Migration):

    dependencies = [
        ('nalkinscloud_mosquitto', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_device_types),
        migrations.RunPython(create_device_models),
    ]
