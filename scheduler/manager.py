from lazyuselessbot.bot import CustomBot
from scheduler.database import SchedulerDatabase

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
from logging import getLogger, WARNING
from json import load


class CustomScheduler():
    def __init__(self, bot: CustomBot, database: SchedulerDatabase):
        self.bot = bot
        self.database = database
        self.scheduler = BlockingScheduler()
        self.logger = getLogger(__name__)

    def disable_apscheduler_logger(self):
        """ Optional """
        getLogger('apscheduler.scheduler').setLevel(WARNING)
        getLogger('apscheduler.executors.default').setLevel(WARNING)

    def load_settings(self, filename: str):
        with open(file=filename, mode='r', encoding='utf-8') as settings_file:
            settings: dict = load(settings_file)

        self.default_group_id: int = settings.get('test_group_id')

    def send_and_delete_message(self, payload: dict):
        payload.get('message').update(
            text='\n'.join(payload.get('message').get('text')))
        message_id = self.bot.send_message(
            chat_id=self.default_group_id, **payload.pop('message'))
        kwargs = {
            'chat_id': self.default_group_id,
            'message_id': message_id
        }
        run_date = datetime.now() + timedelta(**payload.pop('timedelta'))
        self.scheduler.add_job(self.bot.delete_message,
                               trigger="date", run_date=run_date, kwargs=kwargs)

    def timeout_job_manager(self, payload: dict):
        if payload.pop('action') == 'send_and_delete_message':
            self.send_and_delete_message(payload)

    def create_job(self, job: dict):
        self.scheduler.add_job(func=self.timeout_job_manager,
                               kwargs=job, **job.pop('time'))

    def create_jobs(self):
        for job in self.database.get_all_jobs():
            self.create_job(job)

    def start(self):
        self.logger.info('Custom Scheduler started')
        self.scheduler.start()

    def stop(self):
        self.logger.info('Custom Scheduler has been shut down')
        self.scheduler.shutdown()
