from json import load, dump
from datetime import datetime


class SchedulerDatabase():
    def __init__(self, settings_filename: str):
        self.database = list()
        self.filename = settings_filename

    def load_database(self):
        with open(self.filename, 'r', encoding='utf-8') as database_file:
            self.database: list = load(database_file)

    def get_all_jobs(self):
        return self.database

    def add_job(self, job: dict):
        self.database.append(job)
        self.save_database_to_file()

    def remove_job(self, job: dict):
        self.database.remove(job)
        self.save_database_to_file()

    def update_job(self, old_job: dict, new_job: dict):
        self.remove_job(old_job)
        self.add_job(new_job)
        self.save_database_to_file()

    def save_database_to_file(self):
        with open(self.filename, 'r', encoding='utf-8') as database_file:
            dump(self.database, database_file, indent=4)
