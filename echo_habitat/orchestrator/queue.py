from celery import Celery
import os

BROKER = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
app = Celery("echo_habitat", broker=BROKER, backend=BACKEND)
app.conf.task_queues = {
    "default": {},
    "codegen": {},
    "tester": {},
    "attestor": {},
    "storyteller": {},
}
