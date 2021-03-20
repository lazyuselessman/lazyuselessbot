from threading import Lock
from json import load, dump


yes = 'yes'
y_symbol = '👍'
y_counter = 'y_counter'
y_list = 'y_list'
no = 'no'
n_symbol = '👎'
n_counter = 'n_counter'
n_list = 'n_list'


class VoteDatabase():
    def __init__(self, filename: str):
        self.lock: Lock = Lock()
        self.database: dict = {}
        self.filename: str = filename
        self.load_database()

    def load_database(self):
        with self.lock:
            with open(self.filename, 'r', encoding='utf-8') as database:
                self.database = load(database)

    def get_current_vote(self, entry: dict, chat_id: int):
        if chat_id in entry[y_list]:
            return yes
        elif chat_id in entry.get(n_list):
            return no

    def remove_from(self, entry: dict, chat_id: int, vote: str):
        if vote == yes:
            entry.get(y_list).remove(chat_id)
            entry[y_counter] -= 1
        elif vote == no:
            entry.get(n_list).remove(chat_id)
            entry[n_counter] -= 1
        elif vote == None:
            return ''
        return f'Removed vote {vote}.\n'

    def add_to(self, entry: dict, chat_id: int, data: str):
        if data == yes:
            entry.get(y_list).append(chat_id)
            entry[y_counter] += 1
        elif data == no:
            entry.get(n_list).append(chat_id)
            entry[n_counter] += 1
        return f'Added vote {data}.'

    def get_entry(self, key: str):
        entry = self.database.get(key)
        if entry is None:
            self.database[key] = {
                y_counter: 0,
                y_list: [],
                n_counter: 0,
                n_list: []
            }
            entry = self.database.get(key)
        return entry

    def edit_entry(self, key: str,  chat_id: int, data: str):
        with self.lock:
            text = str()
            entry: dict = self.get_entry(key)
            vote = self.get_current_vote(entry, chat_id)
            text += self.remove_from(entry, chat_id, vote)
            if vote != data:
                text += self.add_to(entry, chat_id, data)
            return (entry.get(y_counter), entry.get(n_counter), text)

    def delete_entry(self, key: str):
        with self.lock:
            return self.database.pop(key, {})

    def save_database(self):
        with self.lock:
            with open(self.filename, 'w', encoding='utf-8') as database:
                dump(self.database, database, indent=4)
