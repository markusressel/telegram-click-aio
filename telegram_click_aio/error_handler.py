from aiogram.types import Message, ParseMode

from telegram_click_aio.permission.base import Permission
from telegram_click_aio.util import send_message


class ErrorHandler:
    """
    Interface for error handlers
    """

    async def on_permission_error(self, message: Message, permissions: Permission) -> bool:
        """
        This method is called when a user tries to execute a command without permission
        :param message: Message
        :param permissions: the permissions, at least one of which was missing
        :return: True if the error was handled, false otherwise
        """
        return False

    async def on_validation_error(self, message: Message, exception: Exception,
                                  help_message: str) -> bool:
        """
        This method is called when an exception is raised during
        argument user input validation.
        :param message: Message
        :param exception: the exception
        :param help_message: help message for the command that failed validation
        :return: True if the error was handled, false otherwise
        """
        return False

    async def on_execution_error(self, message: Message, exception: Exception) -> bool:
        """
        This method is called when an exception is raised during
        the execution of a command
        :param message: Message
        :param exception: the exception
        :return: true if the error was handled, false otherwise
        """
        return False


class DefaultErrorHandler(ErrorHandler):
    DEFAULT_PERMISSION_DENIED_MESSAGE = ":stop_sign: You do not have permission to use this command."

    def __init__(self, silent_denial: bool = True, print_error: bool = False):
        """
        Creates an instance
        :param silent_denial: Whether to silently ignore commands from users without permission
        :param print_error: Whether to print a stacktrace on execution errors
        """
        self.silent_denial = silent_denial
        self.print_error = print_error

    async def on_permission_error(self, message: Message, permissions: Permission) -> bool:
        bot = message.bot
        chat_id = message.chat.id

        if not self.silent_denial:
            # send 'permission denied' message
            text = self.DEFAULT_PERMISSION_DENIED_MESSAGE
            await send_message(bot, chat_id=chat_id, message=text,
                               parse_mode=ParseMode.MARKDOWN,
                               reply_to=message.message_id)

        return True

    async def on_validation_error(self, message: Message, exception: Exception,
                                  help_message: str) -> bool:
        bot = message.bot
        chat_id = message.chat.id

        denied_text = "\n".join([
            ":exclamation: `{}`".format(str(exception)),
            "",
            help_message
        ])
        await send_message(bot, chat_id=chat_id,
                           message=denied_text,
                           parse_mode=ParseMode.MARKDOWN,
                           reply_to=message.message_id)
        return True

    async def on_execution_error(self, message: Message, exception: Exception) -> bool:
        bot = message.bot
        chat_id = message.chat.id

        if self.print_error:
            import traceback
            exception_text = "\n".join(list(map(lambda x: "{}:{}\n\t{}".format(x.filename, x.lineno, x.line),
                                                traceback.extract_tb(exception.__traceback__))))
            denied_text = ":boom: `{}`".format(exception_text)
        else:
            denied_text = ":boom: There was an error executing your command :worried:"
        await send_message(bot, chat_id=chat_id,
                           message=denied_text,
                           parse_mode=ParseMode.MARKDOWN,
                           reply_to=message.message_id)
        return True


DEFAULT_ERROR_HANDLER = DefaultErrorHandler()
