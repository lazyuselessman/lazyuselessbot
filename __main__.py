from telegram_bot.lazyuselessbot import CustomTelegramBot
from scheduler.scheduler_manager import CustomScheduler

import logging
from logging import Logger, INFO, getLogger, StreamHandler, FileHandler, Formatter
from locale import setlocale, LC_ALL
from threading import Thread
from datetime import datetime


def configure_logger():
    # O?ieyia?y (ceia) → Фінляндія (зима)
    setlocale(LC_ALL, '')
    formatter: Formatter = Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s - %(name)s',
                                     datefmt='%a, %d %b %Y %H:%M:%S %z %Z')

    logger: Logger = getLogger()
    logger.setLevel(INFO)

    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # f'./logs/{datetime.now().strftime("file_%d_%m_%Y_%H_%M.log")}'
    file_handler = FileHandler(filename=f'./logs/file.log',
                               mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def configure_telegram_bot():
    telegram_bot = CustomTelegramBot()
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
    configure_logger()
    telegram_bot: CustomTelegramBot = configure_telegram_bot()
    scheduler: CustomScheduler = configure_scheduler(telegram_bot)
    display_simple_menu(telegram_bot, scheduler)


if __name__ == '__main__':
    main()
