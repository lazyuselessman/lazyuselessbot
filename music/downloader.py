import os
from time import sleep
from youtube_dl import YoutubeDL
from urllib.parse import urlparse
from urllib.request import urlretrieve


class MusicDownloader():
    def __init__(self):
        pass

    def get_ydl_options(self, filename: str) -> dict:
        return {
            'quiet': True,
            'format': 'bestaudio/best',
            'outtmpl': f'{filename}.%(ext)s',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        }

    def download_audio(self, info: dict, filename: str):
        ydl_opts = self.get_ydl_options(filename)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([info.get('webpage_url')], )
            return f'{filename}.mp3'

    def verify_audio_parameters(self, info: dict):
        duration = 10 * 60
        filesize = 50 * 1024 * 1024
        if info.get('duration', 0) > duration:
            raise NameError(f'Audio duration exceed {duration} seconds.')
        if info.get('filesize', 0) > filesize:
            raise NameError(f'Audio filesize exceed {filesize} bytes.')

    def song(self, info: dict, filename: str):
        self.verify_audio_parameters(info)
        while True:
            try:
                return self.download_audio(info, filename)
            except Exception as err:
                print(f'{err}\n{info.get("webpage_url")}')
                sleep(10)

    def retrive_songs_info(self, url: str) -> list[dict]:
        info = YoutubeDL({'quiet': True}).extract_info(url, download=False)
        if info.get('_type') == 'playlist':
            return info.get('entries')
        return [info, ]

    def thumb(self, url: str, filename: str) -> str:
        _, ext = os.path.splitext(os.path.normpath(urlparse(url).path))
        return urlretrieve(url, f'{filename}{ext}')[0]
