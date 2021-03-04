from telegram_bot.lazyuselessbot import CustomTelegramBot
from scheduler.scheduler_manager import CustomScheduler

from logging import Logger, basicConfig, INFO, getLogger
from locale import setlocale, LC_ALL
from threading import Thread
from datetime import datetime

def configure_logger():
    # O?ieyia?y (ceia) → Фінляндія (зима)
    setlocale(LC_ALL, '')
    basicConfig(format='%(asctime)s - %(levelname)s - %(message)s - %(name)s',
                level=INFO,
                datefmt='%a, %d %b %Y %H:%M:%S %z %Z',
                filename=f'./logs/file.log', #f'./logs/{datetime.now().strftime("file_%d_%m_%Y_%H_%M.log")}',
                filemode='w')
    return getLogger(__name__)


def configure_telegram_bot(logger):
    telegram_bot = CustomTelegramBot(logger)
    telegram_bot_thread = Thread(target=telegram_bot.start)
    telegram_bot_thread.start()
    return telegram_bot


def configure_scheduler(telegram_bot: CustomTelegramBot):
    scheduler = CustomScheduler(telegram_bot)
    scheduler_thread = Thread(target=scheduler.start)
    scheduler_thread.start()
    return scheduler


def display_simple_menu(telegram_bot: CustomTelegramBot, scheduler: CustomScheduler):
    while True:
        option = input('Simple menu:\n0. Stop bot polling.\n')
        if option == '0':
            scheduler.stop()
            telegram_bot.stop()
            break


def main():
    logger: Logger = configure_logger()
    telegram_bot: CustomTelegramBot = configure_telegram_bot(logger)
    scheduler: CustomScheduler = configure_scheduler(telegram_bot)
    display_simple_menu(telegram_bot, scheduler)


if __name__ == '__main__':
    main()
