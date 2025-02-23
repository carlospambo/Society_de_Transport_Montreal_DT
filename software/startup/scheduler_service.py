import logging
import uuid
from logging import Logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class SchedulerService:

    def __init__(self, execute_func, trigger: CronTrigger = None, job_id:str = None, logger: Logger = None, verbose: bool = True):
        self._func = execute_func
        self._trigger = CronTrigger(hour="*", second=30) if not trigger else trigger # schedule the cron job to run every 30 seconds
        self._l = logging.getLogger("SchedulerService") if not logger else logger
        self._verbose = verbose
        self._job_id = str(uuid.uuid4()) if not job_id else job_id
        self._scheduler = BackgroundScheduler()

    def start(self):
        if self._func:
            self._scheduler.add_job(func=self._func, trigger=self._trigger, id=self._job_id)
            self._scheduler.start()
        else:
            self._l.error("Empty function provided to the scheduler")


    def stop(self):
        self._scheduler.remove_job(self._job_id)


if __name__ == '__main__':
    service = SchedulerService(None)
    service.start()