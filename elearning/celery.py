# elearning/celery.py
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings')

app = Celery('elearning', broker='redis://localhost:6379/0')

# pull in config from Django settings, CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# auto-discover tasks.py modules in all INSTALLED_APPS
app.autodiscover_tasks()
