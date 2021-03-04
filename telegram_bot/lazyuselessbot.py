from telegram.ext import Updater, Dispatcher
from telegram import Bot, Message
from logging import Logger
from pprint import pprint
from json import load


class CustomTelegramBot():
    def __init__(self, logger: Logger):
        self.logger: Logger = logger

        self.load_settings()
        self.preparation()
        self.setup_handlers()

    def load_settings(self):
        with open(file='telegram_bot/telegram_bot_settings.json', mode='r') as settings_file:
            settings: dict = load(settings_file)

        self.token: str = settings.get('token')
        self.owner_chat_id: int = settings.get('owner_chat_id')
        self.owner_group_id: int = settings.get('owner_group_id')

    def preparation(self):
        self.updater: Updater = Updater(token=self.token, use_context=True)
        self.dp: Dispatcher = self.updater.dispatcher
        self.bot: Bot = self.updater.bot

    def setup_handlers(self):

        pass

    def send_message(self, chat_id, **kwargs):
        message: Message = self.bot.send_message(chat_id=chat_id, **kwargs)
        return message.message_id

    def delete_message(self, chat_id, message_id):
        self.bot.delete_message(chat_id=chat_id, message_id=message_id)

    def start(self):
        self.updater.start_polling()  # timeout=999

    def stop(self):
        self.updater.stop()
