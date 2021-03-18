from telegram.ext import Updater, Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram.ext.filters import Filters
from telegram import Bot, Message, Update, Chat, ChatAction
from logging import getLogger, Logger
from json import load

from music.music_model import ModelMusic


class CustomBot():
    def __init__(self, music_downloader: ModelMusic):
        self.logger: Logger = getLogger(__name__)
        self.music_downloader = music_downloader

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
        # basic commands
        self.dp.add_handler(CommandHandler('start', self.start_message))
        self.dp.add_handler(CommandHandler('help', self.help_message))

        # music download, scheduler access from web
        self.dp.add_handler(CommandHandler('music', self.music))
        self.dp.add_handler(CommandHandler('time', self.time))

        # download income audio
        self.dp.add_handler(MessageHandler(Filters.audio, self.audio))

        # callback for query
        self.dp.add_handler(MessageHandler(Filters.all, self.all))

        # default answer
        self.dp.add_handler(CallbackQueryHandler(self.callback))

        # error handler
        self.dp.add_error_handler(self.error)

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

    def time(self, update: Update, context: CallbackContext):
        pass

    def audio(self, update: Update, context: CallbackContext):
        pass

    def all(self, update: Update, context: CallbackContext):
        pass

    def callback(self, update: Update, context: CallbackContext):
        pass

    def error(self, update: Update, context: CallbackContext):
        self.logger.error(f'Update {update} caused error {context.error}')

    def send_message(self, chat_id, **kwargs):
        self.bot.send_chat_action(chat_id, ChatAction.TYPING)
        message: Message = self.bot.send_message(chat_id=chat_id, **kwargs)
        return message.message_id

    def send_audio(self, chat_id, **kwargs):
        self.bot.send_chat_action(chat_id, ChatAction.UPLOAD_AUDIO)
        return self.bot.send_audio(**kwargs)

    def delete_message(self, chat_id, message_id):
        self.bot.delete_message(chat_id=chat_id, message_id=message_id)

    def start(self):
        self.logger.info('Custom Bot started')
        self.updater.start_polling()  # timeout=999

    def stop(self):
        self.logger.info('Custom Bot has been shut down')
        self.updater.stop()
