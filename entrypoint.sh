#!/bin/bash

cd /nalkinscloud-api

echo "#######################" 2>&1
echo "Start Models Migrations" 2>&1
echo "#######################" 2>&1
echo Migrate Models
python3.6 manage.py makemigrations
python3.6 manage.py migrate

#echo Collect static files
#python3.6 manage.py collectstatic --no-input

echo "#####################" 2>&1
echo "Start Gunicorn server" 2>&1
echo "#####################" 2>&1
exec gunicorn nalkinscloud_django.wsgi:application --log-level=DEBUG -b 0.0.0.0:8000