from mutagen.id3 import TIT2, TPE1, TDRC, TCON, TALB, TRCK, COMM
from unicodedata import normalize
from mutagen.mp3 import MP3
from json import load, dump
from os import rename

# id  | youtube_id    | filename  | telegram_id   | duration  | performer         | Title         | thumb
# 0   | xxxxxxxxxxxx  | temp_.mp3 | 1235          | 120       | Three Days Grace  | The Real You  | cover.jpeg


class MusicDatabase():
    def __init__(self):
        pass

    def load_settings(self, filename: str):
        with open(filename, 'r') as settings:
            settings = load(settings)
        self.path = settings.get('path')
        self.temp_filename = settings.get('temp_filename')

    def audio_exist(self, info: dict):
        self.dump_info(info)
        return None

    def update_record(self, telegram_id: str):
        # record.update(telegram_id=telegram_id)
        pass

    def add_audio(self, audio: str, info: dict):
        filename = self.generate_filename(info)
        filename = self.normalize_filename(filename)
        filename = f'{self.path}{filename}'
        try:
            rename(f'{self.path}{audio}', filename, )
        except:
            pass
        self.add_audio_tags(filename, info)
        record = {
            'youtube_id': info.get('id'),
            'filename': filename,
            'telegram_id': '',
            'duration': f'{info.get("duration", 0)}',
            'performer': info.get('artist'),
            'title': info.get('track'),
            # 'thumb': info.get('thumbnail')
        }
        return record

    def generate_filename(self, info: dict):
        # %(artist)s%(track)s
        # %(uploader)s%(title)s
        # otherwise search on MusicBrainz
        filename = f'{info.get("artist", "NA")} - {info.get("track", "NA")}'
        if filename == 'NA - NA':
            filename = f'{info.get("uploader", "NA")} - {info.get("title", "NA")}'
        # elif 'NA -' in filename or '- NA':
            # print(f'Press F to pay respect before getting information from MusicBrainz.')
        return f'{filename}.mp3'

    def normalize_filename(self, filename: str):
        return normalize('NFKD', filename).encode('cp1251', 'ignore').decode('cp1251')

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
