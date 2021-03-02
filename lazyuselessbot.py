from json import load
from telegram.ext import Updater, Dispatcher
from logging import Logger


class CustomTelegramBot():
    def __init__(self, logger: Logger):
        self.logger: Logger = logger

        self.load_settings()
        self.preparation()
        self.setup_handlers()

    def load_settings(self):
        with open(file='telegram_bot_settings.json', mode='r') as settings_file:
            settings: dict = load(settings_file)
        
        self.token: str = settings.get('token')
        self.owner_chat_id: int = settings.get('owner_chat_id')
        self.group_chat_id: int = settings.get('group_chat_id')
        
    def preparation(self):
        self.updater: Updater = Updater(token=self.token, use_context=True)
        self.dp: Dispatcher = self.updater.dispatcher

    def setup_handlers(self):

        pass

    def get_updater(self):
        return self.updater

    def start(self):
        self.updater.start_polling(timeout=999)

    def stop(self):
        self.updater.stop()
