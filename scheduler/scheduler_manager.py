from telegram_bot.lazyuselessbot import CustomTelegramBot

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
from logging import getLogger, WARNING
from json import load


class CustomScheduler():
    def __init__(self, telegram_bot: CustomTelegramBot):
        self.telegram_bot = telegram_bot
        self.scheduler = BlockingScheduler()

        self.get_logger()
        self.disable_apscheduler_logger()
        self.load_settings()
        self.load_database()
        self.create_jobs()

    def get_logger(self):
        self.logger = getLogger(__name__)

    def disable_apscheduler_logger(self):
        getLogger('apscheduler.scheduler').setLevel(WARNING)

    def load_settings(self):
        with open('scheduler/scheduler_settings.json', 'r') as settings_file:
            settings: dict = load(settings_file)

        self.database_filename: str = settings.get('database_filename')
        self.default_group_id: int = settings.get('default_group_id')

    def load_database(self):
        with open(self.database_filename, 'r') as database_file:
            self.database: dict = load(database_file)

    def send_and_delete_message(self, payload: dict):
        payload.get('message').update(
            text='\n'.join(payload.get('message').get('text')))
        message_id = self.telegram_bot.send_message(
            chat_id=self.default_group_id, **payload.pop('message'))
        kwargs = {
            'chat_id': self.default_group_id,
            'message_id': message_id
        }
        run_date = datetime.now() + timedelta(**payload.pop('timedelta'))
        self.scheduler.add_job(self.telegram_bot.delete_message,
                               trigger="date", run_date=run_date, kwargs=kwargs)

    def timeout_job_manager(self, payload: dict):
        if payload.pop('action') == 'send_and_delete_message':
            self.send_and_delete_message(payload)

    def create_job(self, job: dict):
        self.scheduler.add_job(func=self.timeout_job_manager,
                               kwargs=job, **job.pop('time'))

    def create_jobs(self):
        for job in self.database:
            self.create_job(job)

    def start(self):
        self.logger.info('Custom Scheduler started')
        self.scheduler.start()

    def stop(self):
        self.logger.info('Custom Scheduler has been shut down')
        self.scheduler.shutdown()
