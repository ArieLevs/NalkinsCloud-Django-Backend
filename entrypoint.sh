#!/bin/sh -e

cd /nalkinscloud-api

echo "#######################" 2>&1
echo "Start Models Migrations" 2>&1
echo "#######################" 2>&1
python manage.py makemigrations
python manage.py migrate

#echo "####################" 2>&1
#echo "Collect Static Files" 2>&1
#echo "####################" 2>&1
#python manage.py collectstatic --no-input

echo "#####################" 2>&1
echo "Start Gunicorn server" 2>&1
echo "#####################" 2>&1
exec gunicorn nalkinscloud_django.wsgi:application --log-level=DEBUG -b 0.0.0.0:8000
