#!/bin/bash

echo Collect static files

cd /nalkinscloud

exec python3.6 manage.py collectstatic --no-input
