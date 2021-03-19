from typing import Callable, TypeVar, Union

from telegram import Update
from telegram.ext import CommandHandler, BaseFilter, Filters
from telegram.utils.types import SLT
from telegram.utils.helpers import DefaultValue, DEFAULT_FALSE

RT = TypeVar('RT')

class CustomCommandHandler(CommandHandler):
    def __init__(
        self,
        command: SLT[str],
        callback: Callable[[Update, 'CallbackContext'], RT],
        filters: BaseFilter = None,
        allow_edited: bool = None,
        pass_args: bool = False,
        pass_update_queue: bool = False,
        pass_job_queue: bool = False,
        pass_user_data: bool = False,
        pass_chat_data: bool = False,
        run_async: Union[bool, DefaultValue] = DEFAULT_FALSE,
    ):
        super().__init__(
            command,
            callback,
            # filters=filters,
            allow_edited=allow_edited,
            pass_args=pass_args,
            pass_update_queue=pass_update_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data,
            pass_chat_data=pass_chat_data,
            run_async=run_async,
        )

        if filters:
            self.filters = Filters.update.message | Filters.update.channel_post | filters
        else:
            self.filters = Filters.update.message | Filters.update.channel_post
