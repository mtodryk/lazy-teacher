import os

from celery import Celery
from celery.signals import worker_process_init

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")

app = Celery("lazy_teacher")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@worker_process_init.connect
def init_worker_process(**kwargs):
    from documents.services.chroma_client import warmup_embedding_model

    warmup_embedding_model()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
