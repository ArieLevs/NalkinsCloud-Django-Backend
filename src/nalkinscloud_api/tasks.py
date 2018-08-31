
from scheduler.celery import *


@app.task
def add(x, y):
    return x + y
