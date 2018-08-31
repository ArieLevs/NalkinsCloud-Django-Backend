
from django.http import HttpResponse
from nalkinscloud_api.tasks import add


def add_req(request):
    a = request.GET.get('a', '0')
    b = request.GET.get('b', '0')
    tmp = add.apply_async((a, b), countdown=10, expires=120)
    return HttpResponse(tmp)
