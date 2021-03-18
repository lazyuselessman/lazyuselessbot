from mutagen.id3 import TIT2, TPE1, TDRC, TCON, TALB, TRCK, COMM
from music.database_model import ModelMusicDatabase
from unicodedata import normalize
from youtube_dl import YoutubeDL
from json import load, dump
from mutagen.mp3 import MP3
from os.path import splitext


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
        filename = f'{info.get("artist", "NA")} - {info.get("track", "NA")}'
        if filename == 'NA - NA':
            filename = f'{info.get("uploader", "NA")} - {info.get("title", "NA")}'
        # elif 'NA -' in filename or '- NA':
            # print(f'Press F to pay respect before getting information from MusicBrainz.')
        return f'{filename}'

    def normalize_filename(self, filename: str):
        return normalize('NFKD', filename).encode('cp1251', 'ignore').decode('cp1251')

    def get_ydl_options(self, filename: str):
        return {
            'quiet': True,
            'format': 'bestaudio/best',
            'outtmpl': f'{self.path}{filename}.%(ext)s',
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
            return f'{filename}.mp3'

    def add_audio_tags(self, filename: str, info: dict):
        audio = MP3(filename)
        tags = {
            # Title/songname/content description
            'TIT2': TIT2(encoding=3, text=info.get('track', '')),
            # Lead performer(s)/Soloist(s)
            'TPE1': TPE1(encoding=3, text=info.get('artist', '')),
            # Date
            'TDRC': TDRC(encoding=3, text=f'{info.get("release_year","")}'),
            # Content type (genre)
            'TCON': TCON(encoding=3, text=info.get('genre', '')),
            # Album/Movie/Show title
            'TALB': TALB(encoding=3, text=info.get('album', '')),
            # Track number/Position in set
            'TRCK': TRCK(encoding=3, text=info.get('track_number', '')),
            # Comments
            'COMM': COMM(encoding=3, text=f'https://youtu.be/{info.get("id", "")}'),
        }
        audio.update(tags)
        audio.save()

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
        return self.download_music_from_info(info)

    def download_playlist_from_url(self, url: str):
        songs = list()
        info = self.get_audio_info(url, False)
        for info in info.get('entries'):
            songs.append(self.download_music_from_info(info))
        return songs
