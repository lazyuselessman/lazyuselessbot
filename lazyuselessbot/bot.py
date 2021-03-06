from telegram.ext import Updater, Dispatcher
from telegram import Bot, Message
from logging import getLogger, Logger
from json import load


class CustomBot():
    def __init__(self):
        self.logger: Logger = getLogger(__name__)

    def load_settings(self, filename: str):
        with open(file=filename, mode='r') as settings_file:
            settings: dict = load(settings_file)

        self.token: str = settings.get('token')
        self.owner_chat_id: int = settings.get('owner_chat_id')
        self.owner_group_id: int = settings.get('owner_group_id')

    def connect(self):
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
        self.logger.info('Custom Bot started')
        self.updater.start_polling()  # timeout=999

    def stop(self):
        self.logger.info('Custom Bot has been shut down')
        self.updater.stop()
