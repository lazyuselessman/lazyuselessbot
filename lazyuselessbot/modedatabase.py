from threading import Lock
from json import load, dump

command = 'Command'
prompt = 'Prompt'
music = 'Music'
cancel = 'Cancel'


class ModeDatabase():
    def __init__(self, filename: str):
        self.lock: Lock = Lock()
        self.filename: str = filename
        self.load_database()

    def load_database(self):
        with self.lock:
            with open(self.filename, 'r', encoding='utf-8') as database:
                database = load(database)
            self.command_group_ids: list = database.get('command_group_ids')
            self.prompt_group_ids: list = database.get('prompt_group_ids')
            self.music_group_ids: list = database.get('music_group_ids')

    def generate_text(self, chat_id: int):
        mode = self.get_current_mode(chat_id)
        return f'Current mode: {mode}\nPress buttons below to change.\nPress Cancel to discard changes.'

    def get_current_mode(self, chat_id: int):
        if chat_id in self.command_group_ids:
            return command
        elif chat_id in self.prompt_group_ids:
            return prompt
        elif chat_id in self.music_group_ids:
            return music

    def remove_from(self, chat_id: int, mode: str):
        if mode == command:
            self.command_group_ids.remove(chat_id)
        elif mode == prompt:
            self.prompt_group_ids.remove(chat_id)
        elif mode == music:
            self.music_group_ids.remove(chat_id)
        elif mode == None:
            return ''
        return f'Removed from {mode}.\n'

    def add_to(self, chat_id: int, data: str):
        if data == command:
            self.command_group_ids.append(chat_id)
        elif data == prompt:
            self.prompt_group_ids.append(chat_id)
        elif data == music:
            self.music_group_ids.append(chat_id)
        elif data == cancel:
            return ''
        return f'Added to {data}.'

    def edit_entry(self, chat_id: int, data: str):
        with self.lock:
            text = str()
            mode = self.get_current_mode(chat_id)
            if data != cancel:
                text += self.remove_from(chat_id, mode)
            if mode != data:
                text += self.add_to(chat_id, data)
            return text

    def save_database(self):
        with self.lock:
            db = {
                'command_group_ids': self.command_group_ids,
                'prompt_group_ids': self.prompt_group_ids,
                'music_group_ids': self.music_group_ids
            }
            with open(self.filename, 'w', encoding='utf-8') as database:
                dump(db, database, indent=4)
