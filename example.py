#  Copyright (c) 2019 Markus Ressel
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ParseMode

from telegram_click_aio import generate_command_list
from telegram_click_aio.argument import Argument, Flag
from telegram_click_aio.decorator import command
from telegram_click_aio.error_handler import ErrorHandler
from telegram_click_aio.permission import GROUP_ADMIN, USER_ID, USER_NAME, NOBODY
from telegram_click_aio.permission.base import Permission

logging.getLogger("telegram_click_aio").setLevel(logging.DEBUG)


class MyPermission(Permission):
    async def evaluate(self, message: Message) -> bool:
        from_user = message.from_user

        # do fancy stuff
        return True


class MyErrorHandler(ErrorHandler):
    """
    Example of a custom error handler
    """

    async def on_permission_error(self, message: Message, permissions: Permission) -> bool:
        bot = message.bot
        chat_id = message.chat.id

        text = "YOU SHALL NOT PASS! :hand::mage:"

        from telegram_click_aio.util import send_message
        await send_message(bot, chat_id=chat_id,
                           message=text,
                           reply_to=message.message_id)

        return True

    def on_validation_error(self, message: Message, exception: Exception,
                            help_message: str) -> bool:
        # return False to let the `DefaultErrorHandler` process this
        return False

    def on_execution_error(self, message: Message, exception: Exception) -> bool:
        # do nothing when an execution error occurs
        return True


def hide_whois_if_admin(message: Message):
    user_id = message.from_user.id
    return user_id not in [123456]


class MyBot:
    name = None
    child_count = None

    async def start(self):
        """
        Starts up the bot.
        This means filling the url pool and listening for messages.
        """
        bot = Bot(token=os.environ.get("TELEGRAM_BOT_KEY"))
        me = await bot.get_me()
        me.username
        try:
            dispatcher = Dispatcher(bot=bot)
            await self._setup_message_handlers(dispatcher)
            await dispatcher.start_polling()
        finally:
            await bot.close()

    async def _setup_message_handlers(self, dispatcher: Dispatcher):
        handlers = [
            (self._unknown_command_callback, ['help', 'h']),
            (self._start_command_callback, ['start']),
            (self._whois_command_callback, ['whois']),
            (self._name_command_callback, ['name', 'n']),
            (self._age_command_callback, ['age', 'a']),
            (self._children_command_callback, ['children', 'c']),
            (self._unknown_command_callback, None),
        ]
        for handler in handlers:
            dispatcher.register_message_handler(handler[0], commands=handler[1])

    async def _unknown_command_callback(self, message: Message):
        await self._send_command_list(message)

    # Optionally specify this command to list all available commands
    @command(name=['help', 'h'],
             description='List commands supported by this bot.')
    async def _commands_command_callback(self, message: Message):
        await self._send_command_list(message)

    @command(name='start',
             description='Start bot interaction')
    async def _start_command_callback(self, message: Message):
        await self._send_command_list(message)

    @command(name='whois',
             description='Some easter-egg',
             hidden=hide_whois_if_admin)
    async def _whois_command_callback(self, message: Message):
        bot = message.bot
        chat_id = message.chat.id
        text = message.from_user.id
        await bot.send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN)

    @staticmethod
    async def _send_command_list(message: Message):
        bot = message.bot
        chat_id = message.chat.id
        text = await generate_command_list(message)
        await bot.send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN)

    @command(name=['name', 'n'],
             description='Get/Set a name',
             arguments=[
                 Argument(name=['name', 'n'],
                          description='The new name',
                          validator=lambda x: x.strip(),
                          optional=True,
                          example='Markus'),
                 Flag(
                     name=['flag', 'f'],
                     description="Some flag that changes the command behaviour."
                 ),
                 Flag(
                     name=['flag2', 'F'],
                     description="Some other flag."
                 )
             ])
    async def _name_command_callback(self, message: Message, name: str or None, flag: bool,
                                     flag2: bool):
        bot = message.bot
        chat_id = message.chat.id
        if name is None:
            message = 'Current: {}'.format(self.name)
        else:
            self.name = name
            message = 'New: {}'.format(self.name)
        message += '\n' + 'Flag is: {}'.format(flag)
        message += '\n' + 'Flag2 is: {}'.format(flag2)
        await bot.send_message(chat_id, message)

    @command(name=['age', 'a'],
             description='Set age',
             arguments=[
                 Argument(name=['age', 'a'],
                          description='The new age',
                          type=int,
                          validator=lambda x: x > 0,
                          example='25')
             ],
             permissions=MyPermission() & ~ GROUP_ADMIN & (USER_NAME('markusressel') | USER_ID(123456)))
    async def _age_command_callback(self, message: Message, age: int):
        bot = message.bot
        chat_id = message.chat.id
        await bot.send_message(chat_id, 'New age: {}'.format(age))

    @command(name=['children', 'c'],
             description='Set children amount',
             arguments=[
                 Argument(name=['amount', 'a'],
                          description='The new amount',
                          type=float,
                          validator=lambda x: x >= 0,
                          example='1.57')
             ],
             permissions=NOBODY,
             error_handler=MyErrorHandler())
    async def _children_command_callback(self, message: Message, amount: float or None):
        bot = message.bot
        chat_id = message.chat.id
        if amount is None:
            await bot.send_message(chat_id, 'Current: {}'.format(self.child_count))
        else:
            self.child_count = amount
            await bot.send_message(chat_id, 'New: {}'.format(amount))


if __name__ == '__main__':
    my_bot = MyBot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(my_bot.start())
