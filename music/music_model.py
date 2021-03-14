from music.database_model import ModelMusicDatabase
from unicodedata import normalize
from youtube_dl import YoutubeDL
from json import load, dump


class ModelMusic():
    def __init__(self, database: ModelMusicDatabase):
        self.database = database

    def load_settings(self, filename: str):
        with open(filename, 'r') as settings:
            settings = load(settings)
        self.path = settings.get('path')

    def get_audio_info(self, url: str, noplaylist: bool = False):
        return YoutubeDL({'quiet': True, 'noplaylist': noplaylist}).extract_info(url, download=False)

    def verify_audio_parameters(self, info: dict):
        duration = 10 * 60
        filesize = 50 * 1024 * 1024
        if info.get('duration', 0) > duration:
            raise NameError(f'Audio duration exceed {duration} seconds.')
        if info.get('filesize', 0) > filesize:
            raise NameError(f'Audio filesize exceed {filesize} bytes.')

    def generate_filename(self, info: dict):
        # %(artist)s%(track)s
        # %(uploader)s%(title)s
        # otherwise search on MusicBrainz
        with YoutubeDL({'outtmpl': '%(artist)s - %(track)s'}) as ydl:
            filename = ydl.prepare_filename(info)
        if filename == 'NA - NA':
            with YoutubeDL({'outtmpl': '%(uploader)s - %(title)s'}) as ydl:
                filename = ydl.prepare_filename(info)
        # elif 'NA -' in filename or '- NA':
            # print(f'Press F to pay respect before getting information from MusicBrainz.')
        return f'{filename}.%(ext)s'

    def normalize_filename(self, filename: str):
        return normalize('NFKD', filename).encode('cp1251', 'ignore').decode('cp1251')

    def get_ydl_options(self, filename: str):
        return {
            'quiet': True,
            'format': 'bestaudio/best',
            'outtmpl': f'{self.path}{filename}',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        }

    def download_audio(self, filename: str, info: dict):
        ydl_opts = self.get_ydl_options(filename)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([info.get('webpage_url')], )
            return ydl.prepare_filename(info)

    def add_audio_tags(self, filename: str, info: dict):
        pass

    def dump_info(self, info: dict):
        with open('./testings/info.json', 'w') as info_file:
            dump(info, info_file, indent=4)

    def playlist_check(self, url):
        info = self.get_audio_info(url)
        if info.get('_type') == 'playlist':
            return True
        return False

    def download_music_from_info(self, info: dict):
        self.dump_info(info)
        exist = self.database.audio_exist(info)
        if exist:
            return exist
        else:
            self.verify_audio_parameters(info)
            filename = self.generate_filename(info)
            filename = self.normalize_filename(filename)
            audio = self.download_audio(filename, info)
            self.add_audio_tags(audio, info)
            return self.database.add_audio(audio, info)

    def download_music_from_url(self, url: str):
        info = self.get_audio_info(url, True)
        self.download_music_from_info(info)

    def download_playlist_from_url(self, url: str):
        info = self.get_audio_info(url, False)
        for info in info.get('entries'):
            self.download_music_from_info(info)
