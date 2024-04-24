from lazyuselessbot.bot import CustomBot
from menu.simple_menu import SimpleMenu
from music.downloader import MusicDownloader
from music.database import MusicDatabase

import logging
import threading
import locale
import json

import asyncio


class Controller():
    def __init__(self):
        pass

    def configure_root_logger(self):
        """ Optional """
        # O?ieyia?y (ceia) → Фінляндія (зима)
        locale.setlocale(locale.LC_ALL, '')
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                                      datefmt='%a, %d %b %Y %H:%M:%S %z %Z')

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # f'./logs/{datetime.now().strftime("file_%d_%m_%Y_%H_%M.log")}'
        file_handler = logging.FileHandler(filename=f'./logs/file.log',
                                           mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def configure_bot(self):
        self.bot = CustomBot(self.music_database)
        self.bot.disable_httpx_logger()
        self.bot.load_settings(self.bot_settings_filename)
        self.bot.connect()
        self.bot.setup_handlers()

        loop = asyncio.new_event_loop()
        self.bot_thread = threading.Thread(target=self.bot.start,
                                           args=(loop, ))
        self.logger.info("Starting bot thread..")
        self.bot_thread.start()

    def configure_simple_menu(self):
        self.menu = SimpleMenu(self.bot, self.music_database)

    def configure_music_downloader(self):
        self.music_downloader: MusicDownloader = MusicDownloader()

    def configure_music_database(self):
        self.music_database = MusicDatabase(self.music_downloader)
        self.music_database.load_settings(self.music_settings_filename)
        self.music_database.connect()
        self.music_database.create_table_if_no_exist()

    def display_menu(self):
        self.menu.display_menu()

    def wait_for_threads_to_shutdown(self):
        self.logger.info("Waiting for bot thread to shutdown..")
        self.bot_thread.join()
        self.logger.info("Bot Thread Down.")

    def load_settings(self, filename: str):
        with open(filename, 'r', encoding='utf-8') as settings:
            settings: dict = json.load(settings)

        self.bot_settings_filename = settings.get('bot_settings')
        self.music_settings_filename = settings.get('music_settings')
        self.music_database_filename = settings.get('music_database')


def main():
    controller = Controller()
    controller.load_settings(settings)
    controller.configure_root_logger()
    controller.configure_music_downloader()
    controller.configure_music_database()
    controller.configure_bot()
    controller.configure_simple_menu()
    controller.display_menu()
    controller.wait_for_threads_to_shutdown()


if __name__ == '__main__':
    settings = 'settings.json'
    main()
