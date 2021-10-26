from telegram.ext import (
    Updater,
    Dispatcher,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    CallbackContext
)
from telegram import Bot, Message, Update, Chat, ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext.filters import Filters
from logging import getLogger, Logger
from json import load
from pprint import pformat
from time import time
from shutil import move

from music.downloader import MusicDownloader
from lazyuselessbot.customcommandhandler import CustomCommandHandler
from lazyuselessbot.votedatabase import VoteDatabase, yes, no, y_symbol, n_symbol
from lazyuselessbot.modedatabase import ModeDatabase, command, prompt, music, cancel


class CustomBot():
    def __init__(self, music_downloader: MusicDownloader):
        self.logger: Logger = getLogger(__name__)
        self.music_downloader = music_downloader
        self.timer = time()

    def load_settings(self, filename: str):
        with open(file=filename, mode='r') as settings_file:
            settings: dict = load(settings_file)

        self.token: str = settings.get('token')
        self.owner_chat_id: int = settings.get('owner_chat_id')
        self.owner_group_id: int = settings.get('owner_group_id')

        self.votedatabase = VoteDatabase(settings.get('votedatabase'))
        self.votedatabase.load_database()
        self.music_path = settings.get('music_path')

        self.modedatabase = ModeDatabase(settings.get('modedatabase'))

    def connect(self):
        self.updater: Updater = Updater(token=self.token, use_context=True)
        self.dp: Dispatcher = self.updater.dispatcher
        self.bot: Bot = self.updater.bot

    def setup_handlers(self):
        # log every message
        self.dp.add_handler(MessageHandler(Filters.all, self.log_update))
        group = 1
        # basic commands
        self.dp.add_handler(CommandHandler('start', self.start_message),
                            group=group)
        self.dp.add_handler(CommandHandler('help', self.help_message),
                            group=group)
        # music download, scheduler access from web
        self.dp.add_handler(CustomCommandHandler('music', self.music, ~Filters.status_update),
                            group=group)
        self.dp.add_handler(CommandHandler('time', self.time),
                            group=group)

        # download income audio
        self.dp.add_handler(MessageHandler(Filters.audio, self.audio),
                            group=group)

        # default behavior
        self.dp.add_handler(CustomCommandHandler('settings', self.settings),
                            group=group)
        self.dp.add_handler(CallbackQueryHandler(self.settings_callback, pattern=f'^({command}|{prompt}|{music}|{cancel})$'),
                            group=group)

        # thank message callback
        self.dp.add_handler(CustomCommandHandler('kb_ty', self.kb_thank, ~Filters.status_update),
                            group=group)
        self.dp.add_handler(CustomCommandHandler('kb_rm', self.kb_remove, ~Filters.status_update),
                            group=group)
        self.dp.add_handler(CallbackQueryHandler(self.thank_callback, pattern=f'^({yes}|{no})$'),
                            group=group)

        # error handler
        self.dp.add_error_handler(self.error)

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

    def settings(self, update: Update, connect: CallbackContext):
        # Send Question to select mode
        # All with Prompt — dispaly nice prompt what bot should do with this message
        # Command only — bot will response only messages with commands
        # All Music — bot will assume that messages in group contain only links to music
        # Default — ignore everything, response only on settings@lazyuselessbot
        text = self.modedatabase.generate_text(update.effective_chat.id)
        reply_markup = self.get_settings_reply_markup()
        update.effective_message.reply_text(text, reply_markup=reply_markup)

    def settings_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        text = self.modedatabase.edit_entry(
            update.effective_chat.id, query.data)
        query.answer(text)
        update.effective_message.reply_to_message.delete()
        update.effective_message.delete()

    def start_message(self, update: Update, context: CallbackContext):
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
            'reply_markup': None,
            'timeout': None
        }
        self.send_message(**kwargs)

    def help_message(self, update: Update, context: CallbackContext):
        kwargs = {
            'chat_id': update.effective_chat.id,
            'text': 'Send me youtube link to retrieve audio from it.\n'
                    '/music <link>\n'
                    'Send me audio to share with me your music (◕‿◕✿)'
        }
        self.send_message(**kwargs)

    def upload_music(self, song: dict, chat_id):
        kwargs = {
            'chat_id': chat_id,
            'duration': song.get('duration'),
            'performer': song.get('performer'),
            'title': song.get('title'),
            'caption': f'https://youtu.be/{song.get("youtube_id")}',
            # 'thumb': open(song.get('thumb'), 'rb')
        }
        if song.get('telegram_id'):
            message_kwargs = {
                'chat_id': chat_id,
                'text': f'Already in library\n'
                        f'https://youtu.be/{song.get("youtube_id")}\n'
                        f'Performer: {song.get("performer")}\n'
                        f'Title: {song.get("title")}'
            }
            self.send_message(**message_kwargs)
            kwargs.update(audio=song.get('telegram_id'))
            self.send_audio(**kwargs)
        else:
            with open(song.get('filename'), 'rb') as audio:
                kwargs.update(audio=audio)
                self.bot.send_audio(**kwargs)

    def music_download(self, url: str, chat_id):
        if self.music_downloader.playlist_check(url):
            for song in self.music_downloader.download_playlist_from_url(url):
                self.upload_music(song, chat_id)
        else:
            song = self.music_downloader.download_music_from_url(url)
            self.upload_music(song, chat_id)

    def music(self, update: Update, context: CallbackContext):
        # for each individual link
        for arg in context.args:
            self.music_download(arg, update.effective_chat.id)
        update.effective_message.delete()

    def time(self, update: Update, context: CallbackContext):
        pass

    def audio(self, update: Update, context: CallbackContext):
        self.log_update(update, context)
        audio_file = update.effective_message.audio.get_file()
        filename = audio_file.download()
        move(filename, f'{self.music_path}{filename}')
        file_id = update.effective_message.audio.file_id
        self.bot.send_audio(chat_id=update.effective_chat.id, audio=file_id)
        update.effective_message.delete()

    def log_update(self, update: Update, _: CallbackContext):
        try:
            self.logger.info(f'Income update:\n{pformat(update.to_dict(), indent=4)}')
        except Exception as err:
            pass

    def error(self, update: Update, context: CallbackContext):
        self.log_update(update, context)
        self.logger.error(f'Error: {context.error}')

    def send_message(self, chat_id, **kwargs):
        self.bot.send_chat_action(chat_id, ChatAction.TYPING)
        message: Message = self.bot.send_message(chat_id=chat_id, **kwargs)
        return message.message_id

    def kb_thank(self, update: Update, context: CallbackContext):
        message = update.effective_message
        if message.reply_to_message:
            key = f'{update.effective_chat.id}_{message.reply_to_message.message_id}'
            chat_id = update.effective_chat.id
            y_counter, n_counter, _ = self.votedatabase.edit_entry(key, chat_id)
            reply_markup = self.get_thanks_replymarkup(y_counter, n_counter)
            message.reply_to_message.edit_reply_markup(reply_markup=reply_markup)
        message.delete()

    def kb_remove(self, update: Update, context: CallbackContext):
        message = update.effective_message
        if message.reply_to_message:
            message.reply_to_message.edit_reply_markup()
        message.delete()

    def get_thanks_replymarkup(self, y_count: int, n_count: int):
        keyboard = [
            [
                InlineKeyboardButton(f'{y_count} {y_symbol}', callback_data=yes),
                InlineKeyboardButton(f'{n_count} {n_symbol}', callback_data=no)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def send_message_thank(self, chat_id, **kwargs):
        self.bot.send_chat_action(chat_id, ChatAction.TYPING)
        reply_markup = self.get_thanks_replymarkup(0, 0)
        message: Message = self.bot.send_message(chat_id=chat_id,
                                                 reply_markup=reply_markup, **kwargs)
        return message.message_id

    def thank_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        key = f'{update.effective_chat.id}_{query.message.message_id}'
        chat_id = update.effective_user.id
        data = query.data
        y_counter, n_counter, text = self.votedatabase.edit_entry(key,
                                                                  chat_id, data)

        query.answer(text=text)
        reply_markup = self.get_thanks_replymarkup(y_counter, n_counter)

        if time() - self.timer > 3:
            self.timer = time()
            query.edit_message_reply_markup(reply_markup=reply_markup)

    def send_audio(self, chat_id, **kwargs):
        self.bot.send_chat_action(chat_id, ChatAction.UPLOAD_AUDIO)
        return self.bot.send_audio(**kwargs)

    def delete_message(self, chat_id, message_id):
        # key = f'{chat_id}_{message_id}'
        # entry = self.votedatabase.delete_entry(key)
        # self.logger.info(f'Removed entry: \n {pformat(entry)}')
        self.bot.delete_message(chat_id=chat_id, message_id=message_id)

    def start(self):
        self.logger.info('Custom Bot started')
        self.updater.start_polling(timeout=999)  #

    def stop(self):
        self.votedatabase.save_database()
        self.logger.info('VoteDatabase has been saved')
        self.modedatabase.save_database()
        self.logger.info('ModeDatabase has been saved')
        self.updater.stop()
        self.logger.info('Custom Bot has been shut down')
