from app.celery import app

import logging
logger = logging.getLogger(__name__)


@app.task
def task_send_confirm_code_phone(to: str, confirm_code: str):
    logger.info(f'СМС. На {to} отправлен код {confirm_code}')

