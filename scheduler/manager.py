from lazyuselessbot.bot import CustomBot
from scheduler.database import SchedulerDatabase

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore 
from datetime import datetime, timedelta
from logging import getLogger, WARNING
from os import startfile
from json import load


class CustomScheduler():
    def __init__(self, bot: CustomBot, database: SchedulerDatabase):
        self.bot = bot
        self.database = database
        self.scheduler = BlockingScheduler()
        self.scheduler.add_jobstore(MemoryJobStore(), alias='scheduled')
        self.logger = getLogger(__name__)
        self.actions = [
            ['send_and_delete_message', self.send_and_delete_message],
            ['open_link_with_delay', self.open_link_with_delay]
        ]

    def reload_database(self):
        self.scheduler.remove_all_jobs(jobstore='default')
        self.database.load_database()
        self.create_jobs()
        self.database.load_database()

    def disable_apscheduler_logger(self):
        """ Optional """
        getLogger('apscheduler.scheduler').setLevel(WARNING)
        getLogger('apscheduler.executors.default').setLevel(WARNING)

    def add_delay_job_run_once(self, func, delta, kwargs):
        run_date = datetime.now() + timedelta(**delta)
        self.scheduler.add_job(func=func, trigger="date",
                               run_date=run_date, kwargs=kwargs, jobstore='scheduled')

    def send_message(self, payload):
        payload.get('message').update(
            text='\n'.join(payload.get('message').get('text')))
        return self.bot.send_message_thank(**payload.get('message'))

    def delete_message(self, payload, message_id):
        kwargs = {
            'func': self.bot.delete_message,
            'delta': payload.get('timedelta'),
            "kwargs": {
                'chat_id': payload.get('message').get('chat_id'),
                'message_id': message_id
            }
        }
        self.add_delay_job_run_once(**kwargs)

    def send_and_delete_message(self, payload: dict):
        message_id = self.send_message(payload)
        self.delete_message(payload, message_id)

    def open_link(self, payload: dict):
        kwargs = {
            'func': startfile,
            'delta': payload.get('timedelta'),
            'kwargs': {
                'filepath': payload.get('url')
            }
        }
        self.add_delay_job_run_once(**kwargs)

    def open_zoom_link(self, payload: dict):
        # TODO:
        #  parse link and open through build in app
        #  not though browser it's annoying
        self.open_link(payload)

    def open_link_with_delay(self, payload: dict):
        url = payload.get('url')
        if 'zoom.us' in url:
            self.open_zoom_link(payload)
        else:
            self.open_link(payload)

    def timeout_job_manager(self, payload: list):
        for income_action in payload:
            action = income_action.get('action')

            for action_name, func in self.actions:
                if action == action_name:
                    func(income_action)

    def create_job(self, job: dict):
        self.scheduler.add_job(func=self.timeout_job_manager,
                               kwargs=job, jobstore='default', **job.pop('time'))

    def create_jobs(self):
        for job in self.database.get_all_jobs():
            self.logger.info(f'Processing job with id: {job.get("id")}')
            self.create_job(job)

    def start(self):
        self.logger.info('Custom Scheduler started')
        self.scheduler.start()

    def stop(self):
        self.logger.info('Custom Scheduler has been shut down')
        self.scheduler.shutdown()
