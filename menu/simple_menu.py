from lazyuselessbot.bot import CustomBot
from scheduler.manager import CustomScheduler
from scheduler.database import SchedulerDatabase
from music.database import MusicDatabase
from datetime import MAXYEAR, MINYEAR, datetime, timedelta
from requests import request
from json import load


class SimpleMenu():
    def __init__(self, bot: CustomBot, scheduler: CustomScheduler, scheduler_database: SchedulerDatabase, music_database: MusicDatabase):
        self.bot = bot
        self.scheduler = scheduler
        self.scheduler_database = scheduler_database
        self.music_database = music_database
        self.chats = 'menu/chats.json'

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

    def select_every_week(self):
        period = self.select_int_range(
            'Every nth week?\n1. Every week\n2. Every two week', 1, 2, False)
        if period == 1:
            return '*'
        week_number = datetime.now().isocalendar().week
        next_week = self.select_int_range(
            'Starting from current week?\n1.Yes.\n2.No', 1, 2, False)
        if next_week == 1:
            if week_number % 2 == 0:
                return f'2/{period}'
            else:
                return f'1/{period}'
        else:
            if week_number % 2 == 0:
                return f'1/{period}'
            else:
                return f'2/{period}'

    def scheduled_job(self):
        day_of_week_text = 'day_of_week:\n0. Monday\n1. Thusday\n2. Wednesday\n3. Thursday\n4. Friday\n5. Saturday\n6. Sunday'
        return {
            'trigger': 'cron',
            # 'year': self.select_int_range('year:', MINYEAR, MAXYEAR, True),
            # 'month': self.select_int_range('month:', 1, 12, True),
            # 'day': self.select_int_range('day:', 1, 31, True),
            'week': self.select_every_week(),
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

    def select_chat(self):
        with open(self.chats, mode='r', encoding='utf-8') as chats:
            chats: list = load(chats)
        text = '\n'.join(
            [f"{i} {chat.get('name')}" for i, chat in enumerate(chats)])
        option = self.select_int_range(text, 0, len(chats), False)
        return chats[option].get('id')

    def dialog_send_and_delete_message(self):
        return {
            'action': 'send_and_delete_message',
            'message': {
                'chat_id': self.select_chat(),
                'disable_notification': True if self.select_int_range(f'disable_notification?\n1. True\n2. False', 1, 2, False) == 1 else False,
                'text': self.input_text('Input text message.\nType . to exit.')
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

    def process_week(self, days: dict, week: int):
        for i in range(1, 6):
            if self.select_int_range(f"skip to skip day {i}, 1 to continue", 1, 1, True) is None:
                continue

            day = days.get(f"{i}")
            for lesson in day.get('lessons'):
                time_start = datetime.strptime(lesson.get('time_start'),
                                               '%H:%M:%S')
                text = f'{datetime.strftime(time_start, "%H:%M")} º ‿ º\n{lesson.get("lesson_name")}\n{lesson.get("teacher_name")}\n{lesson.get("lesson_room")}'
                url = input('Adding ' + lesson.get('day_name') +
                            f':\n{text}\nInput conference url: ')
                text += f"\n{url}"
                job: dict = dict()
                job.update(id=self.scheduler_database.get_new_id())
                time_start = time_start - timedelta(minutes=10)
                time_delta = datetime.strptime(lesson.get(
                    'time_end'), '%H:%M:%S') - time_start
                job.update(time={
                    'trigger': 'cron',
                    'week': f'{week}/2',
                    'day_of_week': f'{i-1}',
                    'hour': time_start.hour,
                    'minute': time_start.minute,
                })
                job.update(payload=[{
                    'action': 'send_and_delete_message',
                    "message": {
                        'chat_id': self.select_chat(),
                        "disable_notification": True if self.select_int_range(f'disable_notification?\n1. True\n2. False', 1, 2, False) == 1 else False,
                        "text": text.split('\n')
                    },
                    "timedelta": {
                        "hours": time_delta.seconds // (60*60),
                        "minutes": (time_delta.seconds//60) % 60
                    }
                },
                    {
                        'action': 'open_link_with_delay',
                        'url': url,
                        'timedelta': {
                            'hours': 0,
                            'minutes': 1
                        }
                }])
                self.scheduler_database.add_job(job)

    def group_lessons(self):
        response = request('GET',
                           f'https://api.rozklad.org.ua/v2/groups/{input("Group name? ")}/timetable')
        if response.ok:
            weeks = response.json().get('data').get('weeks')
            self.process_week(weeks.get('1').get('days'), 1)
            self.process_week(weeks.get('2').get('days'), 2)
        else:
            print("Unable to fetch group lessons.")

    def print_database(self):
        self.music_database.print_songs()

    def drop_table(self):
        self.music_database.drop_table()

    def display_menu(self):
        while True:
            option = input('\n'.join(('Simple menu:',
                                      '0. Stop bot polling.',
                                      '1. Add new job to database.',
                                      '2. Reload database.',
                                      '3. Setup group lessons.',
                                      '4. Print music database.',
                                      #   '5. Drop table.',
                                      '')))
            if option == '0':
                self.shutdown()
                break
            elif option == '1':
                self.add_new_job_to_database()
            elif option == '2':
                self.scheduler.reload_database()
            elif option == '3':
                self.group_lessons()
            elif option == '4':
                self.print_database()
            # elif option == '5':
            #     self.drop_table()
