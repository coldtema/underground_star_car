import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'underground_star_car.settings')

app = Celery('underground_star_car')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()