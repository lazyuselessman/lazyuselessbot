from music.database import MusicDatabase
from youtube_dl import YoutubeDL
from json import load


class MusicDownloader():
    def __init__(self, database: MusicDatabase):
        self.database = database

    def load_settings(self, filename: str):
        with open(filename, 'r') as settings:
            settings = load(settings)

        self.path = settings.get('path')
        self.temp_filename = settings.get('temp_filename')

    def get_ydl_options(self):
        return {
            'quiet': True,
            'format': 'bestaudio/best',
            'outtmpl': f'{self.path}{self.temp_filename}.%(ext)s',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        }

    def download_audio(self, info: dict):
        ydl_opts = self.get_ydl_options()
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([info.get('webpage_url')], )
            return f'{self.temp_filename}.mp3'

    def verify_audio_parameters(self, info: dict):
        duration = 10 * 60
        filesize = 50 * 1024 * 1024
        if info.get('duration', 0) > duration:
            raise NameError(f'Audio duration exceed {duration} seconds.')
        if info.get('filesize', 0) > filesize:
            raise NameError(f'Audio filesize exceed {filesize} bytes.')

    def download_music_from_info(self, info: dict):
        exist = self.database.audio_exist(info)
        if exist:
            return exist
        else:
            self.verify_audio_parameters(info)
            audio = self.download_audio(info)
            return self.database.add_audio(audio, info)

    def get_audio_info(self, url: str, noplaylist: bool = False):
        return YoutubeDL({'quiet': True, 'noplaylist': noplaylist}).extract_info(url, download=False)

    def download_music_from_url(self, url: str):
        info = self.get_audio_info(url, True)
        return self.download_music_from_info(info)

    def download_playlist_from_url(self, url: str):
        songs = list()
        info = self.get_audio_info(url, False)
        for info in info.get('entries'):
            songs.append(self.download_music_from_info(info))
        return songs

    def playlist_check(self, url):
        info = self.get_audio_info(url)
        if info.get('_type') == 'playlist':
            return True
        return False
