#!/bin/bash

cd /nalkinscloud

echo Migrate Models
python3.6 manage.py makemigrations
python3.6 manage.py migrate

#echo Collect static files
#python3.6 manage.py collectstatic --no-input

exec gunicorn nalkinscloud_django.wsgi:application --log-level=DEBUG -b 0.0.0.0:8000