from lazyuselessbot import CustomTelegramBot
from threading import Thread
import logging
from logging import Logger


def configure_logger():
    logging.basicConfig(format='%(asctime)s - %(levelname)s\n%(message)s - %(name)s\n',
                        level=logging.INFO,
                        datefmt='%a, %d %b %Y %H:%M:%S %z %Z')
    return logging.getLogger(__name__)


def configure_telegram_bot(logger):
    telegram_bot = CustomTelegramBot(logger)
    telegram_bot_thread = Thread(target=telegram_bot.start)
    telegram_bot_thread.start()
    return telegram_bot


def main():
    logger: Logger = configure_logger()
    telegram_bot: CustomTelegramBot = configure_telegram_bot(logger)

    while True:
        option = input('Simple menu:\n0. Stop bot polling.')
        if option == '0':
            telegram_bot.stop()
            break


if __name__ == '__main__':
    main()
