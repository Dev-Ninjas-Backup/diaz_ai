# app.celery_app.py
# Scheduler for background tasks
from celery import Celery
from celery.schedules import crontab
import os

celery = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

celery.conf.timezone = "Asia/Dhaka"

import app.schedule_task  # Ensure tasks are registered
celery.conf.beat_schedule = {
    "run-at-0525-evryday": {
        "task": "app.tasks.daily_task",
        "schedule": crontab(hour=5, minute=25),  # <-- updated to 4:10 AM
    }
}
