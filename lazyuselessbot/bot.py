from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
)
from telegram import Bot, Message, Update
from telegram.ext import filters
from telegram.constants import ChatAction
import logging
from pprint import pformat
from time import time
from shutil import move

from music.database import MusicDatabase

import asyncio
import json


class CustomBot():
    def __init__(self, music_database: MusicDatabase):
        self.logger = logging.getLogger(__name__)
        self.music_database = music_database
        self.last_action = time()

    def disable_httpx_logger(self):
        logging.getLogger("httpx").setLevel(logging.WARNING)

    def load_settings(self, filename: str):
        with open(filename, mode='r') as settings_file:
            settings: dict = json.load(settings_file)

        self.token: str = settings.get('token')
        self.owner_chat_id: int = settings.get('owner_chat_id')
        self.owner_group_id: int = settings.get('owner_group_id')

        self.music_path = settings.get('music_path')

    def connect(self):
        self.application: Application = ApplicationBuilder().token(self.token).build()
        self.bot: Bot = self.application.bot

    def setup_handlers(self):
        # log every message
        self.application.add_handler(
            MessageHandler(filters.ALL, self.log_update))
        group = 1
        # basic commands
        self.application.add_handler(CommandHandler('start', self.start_message),
                                     group=group)
        self.application.add_handler(CommandHandler('help', self.help_message),
                                     group=group)
        # music download, scheduler access from web
        self.application.add_handler(CommandHandler('music', self.music, filters.UpdateType.MESSAGES | filters.UpdateType.CHANNEL_POST),
                                     group=group)

        # download income audio
        self.application.add_handler(MessageHandler(filters.AUDIO, self.audio),
                                     group=group)

        # error handler
        self.application.add_error_handler(self.error)

    async def check_send_rate(self):
        curtime = time()
        if curtime - self.last_action < 4:
            print(f'Sleeping for {4 - (curtime - self.last_action)}sec')
            await asyncio.sleep(4 - (curtime - self.last_action))
        self.last_action = curtime

    async def start_message(self, update: Update, context: CallbackContext):
        kwargs = {
            'chat_id': update.effective_chat.id,
            'text': 'Greetings º ◡ º\n'
                    'Send me youtube link to retrieve audio from it.\n'
                    '/music <link>\n'
                    'Send me audio to share with me your music (◕‿◕✿)',
            'parse_mode': None,
            'disable_web_page_preview': None,
            'disable_notification': False,
            'reply_to_message_id': None,
            'reply_markup': None
        }
        await self.send_message(**kwargs)

    async def help_message(self, update: Update, context: CallbackContext):
        kwargs = {
            'chat_id': update.effective_chat.id,
            'text': 'Send me youtube link to retrieve audio from it.\n'
                    '/music <link>\n'
                    'Send me audio to share with me your music (◕‿◕✿)'
        }
        await self.send_message(**kwargs)

    async def upload_music(self, song: dict, chat_id):
        kwargs = {
            'duration': song.get('duration'),
            'performer': song.get('performer'),
            'title': song.get('title'),
            'caption': f'https://youtu.be/{song.get("youtube_id")}',
            'thumbnail': open(song.get('thumbnail'), 'rb')
        }
        if song.get('telegram_id'):
            message_kwargs = {
                'chat_id': chat_id,
                'text':
                f'Already in library\n'
                f'https://youtu.be/{song.get("youtube_id")}\n'
                f'Performer: {song.get("performer")}\n'
                f'Title: {song.get("title")}'
            }
            await self.send_message(**message_kwargs)
            kwargs.update(audio=song.get('telegram_id'))
            await self.send_audio(chat_id, **kwargs)
        else:
            with open(song.get('filename'), 'rb') as audio:
                kwargs.update(audio=audio)
                audio_message = await self.send_audio(chat_id, **kwargs)
                self.music_database.update_record(song.get('youtube_id'),
                                                  audio_message.audio.file_id)

    async def music_download(self, url: str, chat_id):
        for song in self.music_database.get_music(url):
            await self.upload_music(song, chat_id)

    async def music(self, update: Update, context: CallbackContext):
        # for each individual link
        for arg in context.args:
            await self.music_download(arg, update.effective_chat.id)
        await self.check_send_rate()
        await update.effective_message.delete()

    async def audio(self, update: Update, context: CallbackContext):
        audio_file = update.effective_message.audio.get_file()
        filename = audio_file.download()
        move(filename, f'{self.music_path}{filename}')
        file_id = update.effective_message.audio.file_id
        await self.check_send_rate()
        await self.bot.send_audio(chat_id=update.effective_chat.id, audio=file_id)
        await self.check_send_rate()
        await update.effective_message.delete()

    async def log_update(self, update: Update, context: CallbackContext):
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        self.logger.info(f'Income update:\n{pformat(update_str, indent=4)}')

    async def error(self, update: Update, context: CallbackContext):
        self.logger.error("\nException while handling an update:"
                          f"\ncontext.chat_data = {str(context.chat_data)}"
                          f"\ncontext.user_data = {str(context.user_data)}", exc_info=context.error)

    async def send_message(self, chat_id, **kwargs):
        await self.check_send_rate()
        await self.bot.send_chat_action(chat_id, ChatAction.TYPING, read_timeout=999)
        await self.check_send_rate()
        message: Message = await self.bot.send_message(chat_id=chat_id, **kwargs, read_timeout=999)
        return message.message_id

    async def send_audio(self, chat_id, **kwargs):
        await self.check_send_rate()
        await self.bot.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO, read_timeout=999)
        await self.check_send_rate()
        return await self.bot.send_audio(chat_id, **kwargs, read_timeout=999)

    def start(self, loop: asyncio.AbstractEventLoop):
        self.logger.info('Custom Bot started')
        self.loop = loop
        asyncio.set_event_loop(loop)
        self.application.run_polling(timeout=999,
                                     read_timeout=999,
                                     write_timeout=999)

    def stop(self):
        async def stop():
            self.application.stop_running()
            self.logger.info('Custom Bot is going to be down')

        asyncio.run_coroutine_threadsafe(stop(), self.loop).result()
