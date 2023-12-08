import os
import contextlib
from json import load, dump
from mutagen.mp3 import MP3
from unicodedata import normalize
from logging import getLogger, Logger
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import exists, update, delete, select
from mutagen.id3 import TIT2, TPE1, TDRC, TCON, TALB, TRCK, COMM

from music.music import Music, Base
from music.downloader import MusicDownloader

# id  | youtube_id    | filename  | telegram_id   | duration  | performer         | Title         | thumb
# 0   | xxxxxxxxxxxx  | temp_.mp3 | 1235          | 120       | Three Days Grace  | The Real You  | cover.jpeg


class MusicDatabase():
    def __init__(self, downloader: MusicDownloader):
        self.logger: Logger = getLogger(__name__)
        self.downloader = downloader

    @contextlib.contextmanager
    def ManagedSession(self):
        session = self.Session()
        try:
            yield session
            session.commit()
            session.flush()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            self.Session.remove()

    def load_settings(self, filename: str):
        with open(filename, 'r') as settings:
            settings = load(settings)
        self.songs_path = settings.get('songs_path')
        self.thumbnails_path = settings.get('thumbnails_path')
        self.music_database = settings.get('music_database')

    def connect(self):
        self.engine = create_engine(self.music_database)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        self.inspector = inspect(self.engine)

    def create_table_if_no_exist(self) -> None:
        if not self.inspector.has_table(Music.__tablename__):
            Base.metadata.create_all(self.engine)

    def drop_table(self) -> None:
        Music.__table__.drop(self.engine)

    def audio_exist(self, youtube_id: str) -> bool:
        with self.ManagedSession() as session:
            return session.query(exists().where(Music.youtube_id == youtube_id)).scalar()

    def delete_song(self, id: int) -> None:
        with self.ManagedSession() as session:
            session.execute(delete(Music).where(Music.id == id))

    def update_record(self, youtube_id: str, telegram_id: str) -> None:
        with self.ManagedSession() as session:
            session.execute(update(Music).
                            where(Music.youtube_id == youtube_id).
                            values(telegram_id=telegram_id))

    def get_music(self, url: str) -> list:
        with self.ManagedSession() as session:
            return [self.get_audio(session, info) for info in self.downloader.retrive_songs_info(url)]

    def get_audio(self, session, info: dict) -> dict:
        music = session.execute(select(Music).
                                where(Music.youtube_id == info.get('id'))).first()
        if music:
            return music[0].to_dict()
        else:
            return self.download_song(session, info).to_dict()

    def download_song(self, session, info: dict) -> Music:
        filename, artist, track = self.generate_filename(info)
        filename = self.normalize_filename(filename)

        song = self.downloader.song(info,
                                    os.path.join(self.songs_path, filename))
        self.add_audio_tags(song, info)

        thumb = self.downloader.thumb(info.get('thumbnail'),
                                      os.path.join(self.thumbnails_path, filename))

        entry = Music(youtube_id=info.get('id'),
                      filename=song,
                      telegram_id='',
                      duration=f'{info.get("duration", 0)}',
                      performer=artist,
                      title=track,
                      thumbnail=thumb)
        session.add(entry)
        self.logger.info(f"Downloaded song id: {info.get('id')}, performer: {artist}, title: {track}")
        return entry

    def generate_filename(self, info: dict):
        # %(artist)s%(track)s
        # %(uploader)s%(title)s
        # otherwise search on MusicBrainz
        artist = info.get("artist", "NA")
        track = info.get("track", "NA")
        filename = f'{artist} - {track}'
        if filename == 'NA - NA':
            artist = info.get("uploader", "NA")
            track = info.get("title", "NA")
            filename = f'{artist} - {track}'
        # elif 'NA -' in filename or '- NA':
            # print(f'Press F to pay respect before getting information from MusicBrainz.')
        return filename, artist, track

    def normalize_filename(self, filename: str):
        for symbol in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            filename = filename.replace(symbol, '')
        return normalize('NFKD', filename).encode('cp1251', 'ignore').decode('cp1251')

    def add_audio_tags(self, filename: str, info: dict):
        audio = MP3(filename)
        tags = {
            # Title/songname/content description
            'TIT2': TIT2(encoding=3, text=f"{info.get('track', '')}"),
            # Lead performer(s)/Soloist(s)
            'TPE1': TPE1(encoding=3, text=f"{info.get('artist', '')}"),
            # Date
            'TDRC': TDRC(encoding=3, text=f"{info.get('release_year','')}"),
            # Content type (genre)
            'TCON': TCON(encoding=3, text=f"{info.get('genre', '')}"),
            # Album/Movie/Show title
            'TALB': TALB(encoding=3, text=f"{info.get('album', '')}"),
            # Track number/Position in set
            'TRCK': TRCK(encoding=3, text=f"{info.get('track_number', '')}"),
            # Comments
            'COMM': COMM(encoding=3, text=f'https://youtu.be/{info.get("id", "")}'),
        }
        audio.update(tags)
        audio.save()

    def print_database(self):
        print('Songs in database:')
        print(f'{"id":>3} | {"youtube_id":>13} | {"filename":>30} | {"telegram_id":>15} | {"duration":>9} | {"performer":>20} | {"title":>10} | {"thumbnail":>30}')
        with self.ManagedSession() as session:
            for song in session.query(Music).order_by(Music.id):
                print(f'{song.id:>3} | {song.youtube_id:>13} | {song.filename:>30} | {song.telegram_id:>15} | {song.duration:>9} | {song.performer:>20} | {song.title:>10} | {song.thumbnail:>30}')

    def print_songs(self):
        print('Songs in database:')
        print(f'{"id":>3} | {"performer":>30} | {"title":>20}')
        with self.ManagedSession() as session:
            for song in session.query(Music).order_by(Music.id):
                print(f'{song.id:>3} | {song.performer:>30} | {song.title:>20}')

    def songs(self):
        with self.ManagedSession() as session:
            return [music.to_dict() for music in session.query(Music).order_by(Music.id)]

    def dump_info(self, info: dict):
        with open('./testings/info.json', 'w') as info_file:
            dump(info, info_file, indent=4)
