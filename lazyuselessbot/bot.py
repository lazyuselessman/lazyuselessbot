from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    CallbackContext,
)
from telegram import Bot, Message, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters
from telegram.constants import ChatAction
import logging
from pprint import pformat
from time import time
from shutil import move

from music.database import MusicDatabase
from lazyuselessbot.votedatabase import VoteDatabase, yes, no, y_symbol, n_symbol
from lazyuselessbot.modedatabase import ModeDatabase, command, prompt, music, cancel

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

        self.votedatabase = VoteDatabase(settings.get('votedatabase'))
        self.votedatabase.load_database()
        self.music_path = settings.get('music_path')

        self.modedatabase = ModeDatabase(settings.get('modedatabase'))

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
        _filters = filters.UpdateType.MESSAGES | filters.UpdateType.CHANNEL_POST
        self.application.add_handler(CommandHandler('music', self.music, _filters),
                                     group=group)
        self.application.add_handler(CommandHandler('time', self.time),
                                     group=group)

        # download income audio
        self.application.add_handler(MessageHandler(filters.AUDIO, self.audio),
                                     group=group)

        # default behavior
        self.application.add_handler(CommandHandler('settings', self.settings),
                                     group=group)
        self.application.add_handler(CallbackQueryHandler(self.settings_callback, pattern=f'^({command}|{prompt}|{music}|{cancel})$'),
                                     group=group)

        # thank message callback
        self.application.add_handler(CommandHandler('kb_ty', self.kb_thank, _filters),
                                     group=group)
        self.application.add_handler(CommandHandler('kb_rm', self.kb_remove, _filters),
                                     group=group)
        self.application.add_handler(CallbackQueryHandler(self.thank_callback, pattern=f'^({yes}|{no})$'),
                                     group=group)

        # error handler
        self.application.add_error_handler(self.error)

    async def check_send_rate(self):
        curtime = time()
        if curtime - self.last_action < 4:
            print(f'Sleeping for {4 - (curtime - self.last_action)}sec')
            await asyncio.sleep(4 - (curtime - self.last_action))
        self.last_action = curtime

    def get_settings_reply_markup(self):
        keyboard = [
            [
                InlineKeyboardButton(command, callback_data=command),
                InlineKeyboardButton(prompt, callback_data=prompt),
                InlineKeyboardButton(music, callback_data=music)
            ],
            [InlineKeyboardButton(cancel, callback_data=cancel)]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def settings(self, update: Update, context: CallbackContext):
        # Send Question to select mode
        # All with Prompt — dispaly nice prompt what bot should do with this message
        # Command only — bot will response only messages with commands
        # All Music — bot will assume that messages in group contain only links to music
        # Default — ignore everything, response only on settings@lazyuselessbot
        text = self.modedatabase.generate_text(update.effective_chat.id)
        reply_markup = self.get_settings_reply_markup()
        await self.check_send_rate()
        await update.effective_message.reply_text(text, reply_markup=reply_markup, reply_to_message_id=update.effective_message.id)

    async def settings_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        text = self.modedatabase.edit_entry(
            update.effective_chat.id, query.data)
        await self.check_send_rate()
        await query.answer(text)
        await self.check_send_rate()
        await update.effective_message.reply_to_message.delete()
        await self.check_send_rate()
        await update.effective_message.delete()

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

    async def time(self, update: Update, context: CallbackContext):
        pass

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

    async def kb_thank(self, update: Update, context: CallbackContext):
        message = update.effective_message
        if message.reply_to_message:
            key = f'{update.effective_chat.id}_{
                message.reply_to_message.message_id}'
            chat_id = update.effective_chat.id
            y_counter, n_counter, _ = self.votedatabase.edit_entry(
                key, chat_id)
            reply_markup = self.get_thanks_replymarkup(y_counter, n_counter)
            await self.check_send_rate()
            await message.reply_to_message.edit_reply_markup(reply_markup=reply_markup)
        await self.check_send_rate()
        await message.delete()

    async def kb_remove(self, update: Update, context: CallbackContext):
        message = update.effective_message
        if message.reply_to_message:
            await self.check_send_rate()
            await message.reply_to_message.edit_reply_markup()
        await self.check_send_rate()
        await message.delete()

    def get_thanks_replymarkup(self, y_count: int, n_count: int):
        keyboard = [
            [
                InlineKeyboardButton(
                    f'{y_count} {y_symbol}', callback_data=yes),
                InlineKeyboardButton(f'{n_count} {n_symbol}', callback_data=no)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def send_message_thank(self, chat_id, **kwargs):
        async def send_message_thank():
            await self.check_send_rate()
            await self.bot.send_chat_action(chat_id, ChatAction.TYPING)
            reply_markup = self.get_thanks_replymarkup(0, 0)
            await self.check_send_rate()
            message: Message = await self.bot.send_message(chat_id=chat_id,
                                                           reply_markup=reply_markup, **kwargs)
            return message.message_id
        return asyncio.run_coroutine_threadsafe(send_message_thank(), self.loop).result()

    async def thank_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        key = f'{update.effective_chat.id}_{query.message.message_id}'
        chat_id = update.effective_user.id
        data = query.data
        y_counter, n_counter, text = self.votedatabase.edit_entry(key,
                                                                  chat_id, data)

        await query.answer(text=text)
        reply_markup = self.get_thanks_replymarkup(y_counter, n_counter)

        await self.check_send_rate()
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    async def send_audio(self, chat_id, **kwargs):
        await self.check_send_rate()
        await self.bot.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO, read_timeout=999)
        await self.check_send_rate()
        return await self.bot.send_audio(chat_id, **kwargs, read_timeout=999)

    def delete_message(self, chat_id, message_id):
        # key = f'{chat_id}_{message_id}'
        # entry = self.votedatabase.delete_entry(key)
        # self.logger.info(f'Removed entry: \n {pformat(entry)}')
        async def delete_message():
            await self.check_send_rate()
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
        asyncio.run_coroutine_threadsafe(delete_message(), self.loop).result()

    def start(self, loop: asyncio.AbstractEventLoop):
        self.logger.info('Custom Bot started')
        self.loop = loop
        asyncio.set_event_loop(loop)
        self.application.run_polling(timeout=999,
                                     read_timeout=999,
                                     write_timeout=999)

    def stop(self):
        async def stop():
            self.votedatabase.save_database()
            self.logger.info('VoteDatabase has been saved')
            self.modedatabase.save_database()
            self.logger.info('ModeDatabase has been saved')
            self.application.stop_running()
            self.logger.info('Custom Bot is going to be down')

        asyncio.run_coroutine_threadsafe(stop(), self.loop).result()
