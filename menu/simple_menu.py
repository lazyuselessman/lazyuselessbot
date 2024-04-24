from lazyuselessbot.bot import CustomBot
from music.database import MusicDatabase


class SimpleMenu():
    def __init__(self, bot: CustomBot, music_database: MusicDatabase):
        self.bot = bot
        self.music_database = music_database

    def shutdown(self):
        print(f'Shutting down..')
        self.bot.stop()

    def print_database(self):
        self.music_database.print_songs()

    def drop_table(self):
        self.music_database.drop_table()

    def delete_music(self):
        self.music_database.print_songs()
        try:
            self.music_database.delete_song(int(input("Input id:")))
        except:
            pass

    def display_menu(self):
        while True:
            option = input('\n'.join(('Simple menu:',
                                      '0. Stop bot polling.',
                                      '1. Print music database.',
                                      #   '2. Drop table.',
                                      '3. Delete song from database.',
                                      '')))
            if option == '0':
                self.shutdown()
                break
            elif option == '1':
                self.print_database()
            # elif option == '2':
            #     self.drop_table()
            elif option == '3':
                self.delete_music()
