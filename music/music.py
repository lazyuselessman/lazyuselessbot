from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Music(Base):
    __tablename__ = 'music'

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_id = Column(String, unique=True)
    filename = Column(String, unique=True)
    telegram_id = Column(String)
    duration = Column(Integer, )
    performer = Column(String)
    title = Column(String)
    thumbnail = Column(String)

    def __repr__(self) -> str:
        return f'<Music(id={self.id}, youtube_id={self.youtube_id}, filename={self.filename}, telegram_id={self.telegram_id}, duration={self.duration}, performer={self.performer}, title={self.title}, thumbnail={self.thumbnail})>'

    def to_dict(self) -> dict:
        return {
            'youtube_id': str(self.youtube_id),
            'filename': str(self.filename),
            'telegram_id': str(self.telegram_id),
            'duration': int(self.duration),
            'performer': str(self.performer),
            'title': str(self.title),
            'thumbnail': str(self.thumbnail)
        }
