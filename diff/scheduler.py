from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from typing import Callable
import logging

logger = logging.getLogger(__name__)


def schedule_job(interval_seconds: int, job: Callable):
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, 'interval', seconds=interval_seconds)
    scheduler.start()
    logger.info('Scheduler started with %d second interval', interval_seconds)
    return scheduler
