# id  | youtube_id    | filename  | telegram_id   | duration  | performer         | Title         | thumb
# 0   | xxxxxxxxxxxx  | rand.mp3  | 1235          | 120       | Three Days Grace  | The Real You  | cover.jpeg


class ModelMusicDatabase():
    def __init__(self):
        pass

    def audio_exist(self, info: dict):
        return None

    def update_record(self, telegram_id: str):
        # record.update(telegram_id=telegram_id)
        pass

    def add_audio(self, audio: str, info: dict):
        record = {
            'youtube_id': info.get('id'),
            'filename': audio,
            'telegram_id': '',
            'duration': f'{info.get("duration", 0)}',
            'performer': info.get('artist'),
            'title': info.get('track'),
            # 'thumb': info.get('thumbnail')
        }
        return record
