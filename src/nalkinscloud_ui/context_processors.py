from datetime import datetime

from django.conf import settings


def metadata(request):
    """
    Add general metadata to template context
    """
    return {
        'project_name': settings.PROJECT_NAME,
        'version': settings.VERSION,
        'current_year': datetime.now().year,  # Pass year to template
        'developer': 'Arie Lev',
        'hostname': settings.HOSTNAME,
        'environment': settings.ENVIRONMENT,
    }
