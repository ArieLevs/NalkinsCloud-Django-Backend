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

The `env` param should be one of: `dev` (sqlite), `alpha`, `prod`  
This is done so the project can be later integrated to CI/CD processes.

Run the project inside a container using:  
`docker run -it -p 8000:8000 nalkinscloud/nalkinscloud-django -p nalkinscloud-django`

Installation
------------
Based on: CentOS Linux 7 Kernel: Linux 3.10.0-693.5.2.el7.x86_64  
**The server will be installed as a dependency for [NalkinsCloud](https://github.com/ArieLevs/NalkinsCloud).**

[Python 3](https://www.python.org/downloads/), 
[Python pip](https://pip.pypa.io/en/stable/installing/) and requirements installation:  
```bash
yum install https://centos7.iuscommunity.org/ius-release.rpm
yum install python36u

yum install python36u-pip
pip3.6 install -r src/requirements.txt
```

Define installation directory `INSTALL_DIR='$HOME'`.
Run `cd $INSTALL_DIR` and NalkinsCloud-Django-Backend `git clone https://github.com/ArieLevs/NalkinsCloud-Django-Backend.git`.  

Provide environment variables:
```bash
env=dev

# Database configs, not needed if 'env=dev'
db_name=''
db_user=''
db_pass=''
db_host=''

# Required for email verifications
email_host=''
email_username=''
email_password=''
email_port=''

django_secret_key=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 50 | head -n 1)

# Optional, send logs to graylog server
graylog_host=''
```

Start server:
```bash
python3.6 src/manage.py makemigrations
python3.6 src/manage.py migrate
python3.6 src/manage.py collectstatic

python3.6 src/manage.py runserver 127.0.0.1:8000
```

Post Installation
-----------------

Create super user `python3.6 src/manage.py createsuperuser`  
Access `https://127.0.0.1/admin`  

Use credential of `superuser` created above, after login access `Applications`
```
Choose:
	Client type: Confidential
	Authorization grant type: Resource owner password-based
	Name: Android (To your choice)
	
	And save
```
An application created so django can serve clients.
