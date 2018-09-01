
FROM python:3.6-alpine

MAINTAINER Arie Lev

ENV PYTHONUNBUFFERED 1
RUN mkdir /nalkinscloud-api
WORKDIR /nalkinscloud-api

# Needed for mysqlclient requirement when using python alpine image
RUN apk add --no-cache mariadb-dev build-base

ADD src /nalkinscloud-api
RUN pip install -r requirements.txt

ADD entrypoint.sh /nalkinscloud-api
RUN chmod +x entrypoint.sh

RUN chmod 755 -R /nalkinscloud-api

ENTRYPOINT ["sh", "/nalkinscloud-api/entrypoint.sh"]
#CMD ["gunicorn", "nalkinscloud_django.wsgi:application", "--log-level=DEBUG", "-b", "0.0.0.0:8000"]
