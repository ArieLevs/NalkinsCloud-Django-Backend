NalkinsCloud-Django-Backend
===========================

This is Django server code, implementing REST API to support [NalkinsCloud](https://github.com/ArieLevs/NalkinsCloud),
The server will connect Android application to MQTT server and database.

Install using Docker
--------------------

Create docker image   
`docker build -t nalkinscloud/nalkinscloud-django .`  

Optional:
 - Tag image for private repo  
    `docker tag nalkinscloud/nalkinscloud-django docker.nalkins.cloud/nalkinscloud/nalkinscloud-django`  
 - Push the image to repository  
    `docker push docker.nalkins.cloud/nalkinscloud/nalkinscloud-django:latest `

The `env` param should be one of: `test` (sqlite), `alpha`, `prod`  
This is done so the project can be later integrated into Jenkins

Run the project inside a container using:  
`docker run -it -p 8000:8000 nalkinscloud/nalkinscloud-django -p nalkinscloud-django`

Installation
------------
Based on: CentOS Linux 7 Kernel: Linux 3.10.0-693.5.2.el7.x86_64  
**The server will be installed as a dependency for [NalkinsCloud](https://github.com/ArieLevs/NalkinsCloud).**

For manual installation you will need to install [Python 3](https://www.python.org/downloads/),
Install by `yum install https://centos7.iuscommunity.org/ius-release.rpm` and then `yum install python36u`
setup [Python pip](https://pip.pypa.io/en/stable/installing/), 
Installed by `yum install python36u-pip`
then run `pip3.6 install Django`,
Additional libraries needed for the code to work `pip3.6 install djangorestframework django-oauth-toolkit mysqlclient apscheduler django-ipware`  

Define installation directory `INSTALL_DIR='$HOME'`, I'm using users home directory for this example

Run `cd $INSTALL_DIR` and create a new project `django-admin startproject django_server`, enter the just created folder `cd $INSTALL_DIR/django_server`, 
And clone NalkinsCloud-Django `git clone https://github.com/ArieLevs/NalkinsCloud-Django.git`.  

Next update `django_server/django_server/settings.py` file  
Append `'oauth2_provider', 'rest_framework',` to `INSTALLED_APPS`

So it will look like this:
```
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'oauth2_provider',
    'rest_framework',
	
	'nalkinscloud',
]
```

Adjust `DATABASES` part with relevant database configurations.  

For example, if your database hosted at `192.168.1.50` and user `django` password for connecting is `12345678`
Then setting.py should look like:  
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_android',
        'USER': 'django',
        'PASSWORD': '12345678',
        'HOST': '192.168.1.50',
        'PORT': '3306',
    }
}
```
* The configurations should point MariaDB, having exact DB structure described on [NalkinsCloud Project](https://github.com/ArieLevs/NalkinsCloud)

Append this to the end of `settings.py` file:
```
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'}
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'YOUR_EMAIL'
EMAIL_HOST_PASSWORD = 'YOUR_EMAIL_PASSWORD'
EMAIL_PORT = 587
```
---------------------

Finally Update `django_server/django_server/urls.py`, so `urlpatterns` will look like:
```
urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^', include('NalkinsCloud.urls')),
    # OAUTH URLS
    url(r'^', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
```

Post Installation
-----------------

Once installed migrate django to MariaDB, `cd $INSTALL_DIR/django_server/` (Project root directory),
Run `python3.6 manage.py makemigrations` and `python3.6 manage.py migrate`
If all went OK, Create super user `python3.6 manage.py createsuperuser`and run the server `python3.6 manage.py runserver 0.0.0.0:80`  
Once server is running access it by browsing the host IP, so if django was installed on host IP `192.168.1.40` access `https://192.168.1.40/admin`  

Use credential of `superuser` created above, after login access `Applications`
```
Choose:
	Client type: Confidential
	Authorization grant type: Resource owner password-based
	Name: Android (To your choice)
	
	And save
```
We have just created an application so django can serve clients  
Please note for 'Client id' and 'Client secret' which are important for our clients to receive tokens.
