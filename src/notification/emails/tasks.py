import logging

from app.celery import app

logger = logging.getLogger(__name__)


@app.task
def task_send_confirm_code_email(to: str, confirm_code: str):
    logger.info(f'Email. На {to} отправлен код {confirm_code}')
