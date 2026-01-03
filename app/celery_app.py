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

celery.conf.update( 
    timezone= "UTC",
    enable_utc= True,


    #connection reliability
    broker_connection_retry_on_startup= True,
    broker_connection_retry= True,
    broker_connection_max_retries= None,
    borker_pool_limit= 10,


    #Task configurations
    task_acks_late=True,
    task_reject_on_worker_lost= True,
    worker_cancel_long_running_tasks_on_connection_loss= True,
    worker_prefetch_multiplier= 4,
    worker_max_tasks_per_child= 1000,


    #Result backed
    result_expire= 3600,
    result_compression= 'gzip',

    # Broker transport options
    broker_transport_options={
        "visibility_timeout": 600,  
        "socket_keepalive": True,
        "socket_connect_timeout": 30,
        "socket_timeout": 30,
        "health_check_interval": 30,
        "max_connections": 50, 
    },
    
    # Result backend transport options
    result_backend_transport_options={
        "socket_keepalive": True,
        "socket_connect_timeout": 30,
        "socket_timeout": 30,
        "max_connections": 50,  
    },


)

import app.schedule_task  # Ensure tasks are registered
celery.conf.beat_schedule = {
    "run-at-0350-evryday": {
        "task": "app.tasks.daily_task",
        "schedule": crontab(hour=3, minute=50),  # <-- updated to 4:10 AM
    }
}
