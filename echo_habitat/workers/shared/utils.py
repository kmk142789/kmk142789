from celery.utils.log import get_task_logger

log = get_task_logger(__name__)


def banner(title: str) -> str:
    return f"\n==== {title} ===="
