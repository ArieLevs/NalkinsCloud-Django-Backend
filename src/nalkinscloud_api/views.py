import logging
import datetime

from nalkinscloud_django.settings import BASE_DIR, PROJECT_NAME
from django.shortcuts import render
from django.http import HttpResponse

# Define logger
default_logger = logging.getLogger(PROJECT_NAME)

# Define global context values
context = {'project_name': 'NalkinsCloud',
           'developer': 'Arie Lev',
           'current_year': datetime.datetime.now().year}  # Pass year to template


# Render main index page
def index(request):
    default_logger.info("index request at: " + str(datetime.datetime.now()))
    default_logger.info(request)

    return render(
        request,
        BASE_DIR + '/templates/index.html',
        context,
        status=HttpResponse.status_code,
    )
