#  Copyright (c) 2019 Markus Ressel
#  .
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  .
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
import asyncio
import functools
import logging
from typing import List

from aiogram.types import Message

from telegram_click_aio import CommandTarget
from telegram_click_aio.argument import Argument
from telegram_click_aio.const import *
from telegram_click_aio.error_handler import ErrorHandler, DEFAULT_ERROR_HANDLER
from telegram_click_aio.help import generate_help_message
from telegram_click_aio.parser import parse_telegram_command, split_command_from_args, split_command_from_target
from telegram_click_aio.permission.base import Permission
from telegram_click_aio.util import find_first, find_duplicates

LOGGER = logging.getLogger(__name__)


async def _check_permissions(message: Message, permissions: Permission) -> bool:
    """
    Checks if a message passes permission tests
    :param message: message
    :param permissions: command permissions
    :return: True if authorized, False otherwise
    """
    if permissions is not None:
        return await permissions.evaluate(message)
    else:
        return True


async def check_command_name_clashes(names: List[str]):
    """
    Checks if a command name has been used multiple times and raises an exception if so
    :param names: command names added in this decorator call
    """
    from telegram_click_aio import COMMAND_LIST

    t = []
    t.extend(map(lambda x: x["names"], COMMAND_LIST))
    t.extend([names])
    t = functools.reduce(list.__add__, t)

    duplicates = find_duplicates(t)
    if len(duplicates) > 0:
        clashing = ", ".join(duplicates.keys())
        raise ValueError("Command names must be unique! Clashing names: {}".format(clashing))


async def check_argument_name_clashes(arguments: List[Argument]):
    """
    Checks if an argument name of a command has been used multiple times and raises an exception if so
    :param arguments: arguments of a command to check
    """
    duplicates = find_duplicates(list(map(lambda x: x.name, arguments)))
    if len(duplicates) > 0:
        clashing = ", ".join(duplicates.keys())
        raise ValueError("Argument names must be unique per command! Clashing arguments: {}".format(clashing))


async def check_optional_argument_after_other(command_name: str, arguments: List[Argument]):
    """
    Checks the order of arguments to make sure no required argument is defined after an optional one
    :param command_name: command name the arguments belong to
    :param arguments: arguments to check
    """
    optional_detected = False
    for arg in arguments:
        if not arg.optional and optional_detected:
            raise AssertionError(
                "Required argument after optional argument in command /{}: {}".format(command_name, arg.name))
        if arg.optional:
            optional_detected = True


def command(name: str or [str], description: str = None,
            arguments: [Argument] = None,
            hidden: bool or callable = None,
            permissions: Permission = None,
            command_target: bytes = CommandTarget.UNSPECIFIED | CommandTarget.SELF,
            error_handler: ErrorHandler = None):
    """
    Decorator to turn a command handler function into a full fledged, shell like command
    :param name: Name of the command
    :param description: a short description of the command
    :param arguments: list of command argument description objects
    :param hidden: whether the command should be hidden from help output
    :param permissions: required permissions to run this command
    :param command_target: command targets to accept
    :param error_handler: a customized error handler
    """
    from telegram_click_aio import COMMAND_LIST

    name = [name] if not isinstance(name, list) else name
    if arguments is None:
        arguments = []

    if hidden is None:
        hidden = False

    loop = asyncio.get_event_loop()

    loop.run_until_complete(check_command_name_clashes(name))
    loop.run_until_complete(check_argument_name_clashes(arguments))
    loop.run_until_complete(check_optional_argument_after_other(name, arguments))

    help_message = loop.run_until_complete(generate_help_message(name, description, arguments))

    COMMAND_LIST.append(
        {
            KEY_NAMES: name,
            KEY_DESCRIPTION: description,
            KEY_ARGUMENTS: arguments,
            KEY_HELP_MESSAGE: help_message,
            KEY_PERMISSIONS: permissions,
            KEY_HIDDEN: hidden
        }
    )

    error_handlers = [DEFAULT_ERROR_HANDLER]
    if error_handler is not None:
        error_handlers.insert(0, error_handler)

    def callback_decorator(func: callable):
        """
        Callback decorator function
        :param func: the function to wrap
        :return: wrapper function
        """

        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            # find function arguments
            message = find_first(args, Message)

            # get bot, chat and message info
            bot = message.bot
            me = await bot.get_me()
            bot_username = me.username
            chat_id = message.chat.id

            try:
                if not await _check_permissions(message, permissions):
                    # permission denied
                    LOGGER.debug("Permission denied in chat {} for user {} for message: {}".format(
                        chat_id, message.from_user.id, message))

                    for handler in error_handlers:
                        if await handler.on_permission_error(message, permissions):
                            break

                    # don't process command
                    return

                # parse and check command target
                cmd, _ = split_command_from_args(message.text)
                _, target = split_command_from_target(bot_username, cmd)
                # check if we are allowed to process the given command target
                if not await filter_command_target(target, bot_username, command_target):
                    LOGGER.debug("Ignoring command for unspecified target {} in chat {} for user {}: {}".format(
                        target, chat_id, message.from_user.id, message))

                    # don't process command
                    return

                try:
                    # parse command and arguments
                    cmd, parsed_args = parse_telegram_command(bot_username, message.text, arguments)
                except ValueError as ex:
                    # error during argument parsing
                    logging.exception("Error parsing command arguments")

                    for handler in error_handlers:
                        if await handler.on_validation_error(message, ex, help_message):
                            break

                    return

                # convert argument names to python param naming convention (snake-case)
                kw_function_args = dict(
                    map(lambda x: (x[0].lower().replace("-", "_"), x[1]), list(parsed_args.items())))
                # execute wrapped function
                return await func(*args, **{**kw_function_args, **kwargs})
            except Exception as ex:
                # error while executing wrapped function
                logging.exception("Error in callback")
                for handler in error_handlers:
                    if await handler.on_execution_error(message, ex):
                        break

        return wrapped

    return callback_decorator


async def filter_command_target(target: str or None, bot_username: str, allowed_targets: bytes):
    """
    Checks if the command target should be accepted based on given input
    :param target: the target of the command or None
    :param bot_username: the username of this bot
    :param allowed_targets: the allowed command target bitmask
    :return: True if allowed, False if not
    """
    if target is None:
        expected = CommandTarget.UNSPECIFIED
    elif target == bot_username:
        expected = CommandTarget.SELF
    else:
        expected = CommandTarget.OTHER

    return expected & allowed_targets == expected
