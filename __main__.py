from lazyuselessbot.bot import CustomBot
from scheduler.manager import CustomScheduler
from scheduler.database import SchedulerDatabase
from menu.simple_menu import SimpleMenu
from music.downloader import MusicDownloader
from music.database import MusicDatabase

from logging import Logger, INFO, getLogger, StreamHandler, FileHandler, Formatter
from locale import setlocale, LC_ALL
from threading import Thread
from datetime import datetime
from json import load


class Controller():
    def __init__(self):
        pass

    def configure_root_logger(self):
        """ Optional """
        # O?ieyia?y (ceia) → Фінляндія (зима)
        setlocale(LC_ALL, '')
        formatter: Formatter = Formatter(fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                                         datefmt='%a, %d %b %Y %H:%M:%S %z %Z')

        logger: Logger = getLogger()
        logger.setLevel(INFO)

        console_handler = StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # f'./logs/{datetime.now().strftime("file_%d_%m_%Y_%H_%M.log")}'
        file_handler = FileHandler(filename=f'./logs/file.log',
                                   mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def configure_bot(self):
        self.bot: CustomBot = CustomBot(self.music_downloader)
        self.bot.load_settings(self.bot_settings_filename)
        self.bot.connect()
        self.bot.setup_handlers()

        bot_thread = Thread(target=self.bot.start)
        bot_thread.start()

    def configure_scheduler_database(self):
        self.scheduler_database: SchedulerDatabase = SchedulerDatabase(
            self.scheduler_database_filename)
        self.scheduler_database.load_database()

    def configure_scheduler(self):
        self.scheduler: CustomScheduler = CustomScheduler(
            self.bot, self.scheduler_database)
        # self.scheduler.disable_apscheduler_logger()
        scheduler_thread = Thread(target=self.scheduler.start)
        scheduler_thread.start()

        self.scheduler.load_settings(self.scheduler_settings_filename)
        self.scheduler.create_jobs()
        self.scheduler_database.load_database()

    def configure_simple_menu(self):
        self.menu = SimpleMenu(self.bot, self.scheduler,
                               self.scheduler_database)

    def configure_music_database(self):
        self.music_database: MusicDatabase = MusicDatabase()
        self.music_database.load_settings(self.music_settings_filename)

    def configure_music_dowloader(self):
        self.music_downloader: MusicDownloader = MusicDownloader(self.music_database)
        self.music_downloader.load_settings(self.music_settings_filename)

    def display_menu(self):
        self.menu.display_menu()

    def load_settings(self, filename: str):
        with open(filename, 'r', encoding='utf-8') as settings:
            settings = load(settings)

        self.bot_settings_filename = settings.get('bot_settings')
        self.scheduler_settings_filename = settings.get('scheduler_settings')
        self.scheduler_database_filename = settings.get('scheduler_database')
        self.music_settings_filename = settings.get('music_settings')
        self.music_database_filename = settings.get('music_database')


def main():
    controller: Controller = Controller()
    controller.load_settings(settings)
    controller.configure_root_logger()
    controller.configure_music_database()
    controller.configure_music_dowloader()
    controller.configure_bot()
    controller.configure_scheduler_database()
    controller.configure_scheduler()
    controller.configure_simple_menu()
    controller.display_menu()


if __name__ == '__main__':
    settings = 'settings.json'
    main()
