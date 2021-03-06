from lazyuselessbot.bot import CustomBot
from scheduler.manager import CustomScheduler
from scheduler.database import SchedulerDatabase
import datetime
from datetime import datetime, MAXYEAR, MINYEAR


class SimpleMenu():
    def __init__(self, bot: CustomBot, scheduler: CustomScheduler, scheduler_database: SchedulerDatabase):
        self.bot = bot
        self.scheduler = scheduler
        self.scheduler_database = scheduler_database

    def shutdown(self):
        print(f'Shutting down..')
        self.scheduler.stop()
        self.bot.stop()

    def select_int_range(self, text: str, min: int, max: int, skip: bool):
        while 1:
            try:
                print(text)
                select = input()
                select_int = int(select)
                if min <= select_int <= max:
                    return select_int
            except ValueError:
                if select == 'exit':
                    self.exit = True
                    return None
                if skip and select == 'skip':
                    return None
                print(f'Select between {min}, {max}.\nType \'exit\' to exit.')
                if skip:
                    print(f'Type \'skip\' to skip.')

    def one_time_job(self):
        year = self.select_int_range('year: ', MINYEAR, MAXYEAR, False)
        month = self.select_int_range('month: ', 1, 12, False)
        day = self.select_int_range('day: ', 1, 31, False)
        hour = self.select_int_range('hour: ', 0, 24, False)
        minute = self.select_int_range('minute: ', 0, 60, False)
        second = self.select_int_range('second: ', 0, 60, False)
        return {
            'trigger': 'date',
            'run_date': f'{year}-{month}-{day}T{hour}:{minute}:{second}'
        }

    def scheduled_job(self):
        day_of_week_text = 'day_of_week:\n0. Monday\n1. Thusday\n2. Wednesday\n3. Thursday\n4. Friday\n5. Saturday\n6. Sunday'
        return {
            'trigger': 'cron',
            # 'year': self.select_int_range('year:', MINYEAR, MAXYEAR, True),
            # 'month': self.select_int_range('month:', 1, 12, True),
            # 'day': self.select_int_range('day:', 1, 31, True),
            'day_of_week': self.select_int_range(day_of_week_text, 0, 6, False),
            'hour': self.select_int_range('hour:', 0, 23, False),
            'minute': self.select_int_range('minute:', 0, 59, False),
            # 'second': self.select_int_range('second:', 0, 59, True)
        }

    def dialog_repeatability(self):
        choice = self.select_int_range(
            f'Repeatability\n1. One time job.\n2. Scheduled.', 1, 2, False)
        if choice == 1:
            return self.one_time_job()
        else:
            return self.scheduled_job()

    def input_text(self, text: str):
        print(text)
        message_text: list = list()
        input_text: str = str()
        while 1:
            input_text = input()
            if input_text == '.':
                return message_text
            message_text.append(input_text)

    def dialog_send_and_delete_message(self):
        return {
            'action': 'send_and_delete_message',
            'message': {
                'disable_notification': True if self.select_int_range(f'disable_notification?\n1. True\n2. False', 1, 2, False) == 1 else False,
                'text': self.input_text('Input text message')
            },
            'timedelta': {
                'hours': self.select_int_range('Delete in:\nhours:', 0, 24, False),
                'minutes': self.select_int_range('Delete in:\nminutes:', 0, 60, False)
            }
        }

    def dialog_open_link_with_delay(self):
        return {
            'action': 'open_link_with_delay',
            'url': input('Input url'),
            'timedelta': {
                'hours': self.select_int_range('Open in:\nhours:', 0, 24, False),
                'minutes': self.select_int_range('Open in:\nminutes:', 0, 60, False)
            }
        }

    def create_action(self):
        text = 'What action?\n1. Send and delete message\n2. Open link with delay'
        choice = self.select_int_range(text, 1, 2, False)
        if choice == 1:
            return self.dialog_send_and_delete_message()
        elif choice == 2:
            return self.dialog_open_link_with_delay()

    def dialog_actions(self):
        actions: list = list()
        while 1:
            choice = self.select_int_range(
                f'Repeatability\n1. Add action.\n2. Finish.', 1, 2, False)
            if choice == 1:
                actions.append(self.create_action())
            else:
                return actions

    def add_new_job_to_database(self):
        print(f'Add new job:')
        job: dict = dict()
        job.update(id=self.scheduler_database.get_new_id())
        job.update(time=self.dialog_repeatability())
        job.update(payload=self.dialog_actions())
        self.scheduler_database.add_job(job)

    def display_menu(self):
        while True:
            option = input(
                'Simple menu:\n0. Stop bot polling.\n1. Add new job to database.\n2. Reload database.\n')
            if option == '0':
                self.shutdown()
                break
            elif option == '1':
                self.add_new_job_to_database()
            elif option == '2':
                self.scheduler.reload_database()
