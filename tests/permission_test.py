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

import datetime

from aiogram.types import Message

from telegram_click_aio.permission.base import Permission
from tests import TestBase


class TruePermission(Permission):
    async def evaluate(self, message: Message):
        return True


class FalsePermission(Permission):
    async def evaluate(self, message: Message):
        return False


def _create_message_mock(chat_id: int = -12345678, chat_type: str = "private", message_id: int = 12345678,
                         user_id: int = 12345678, username: str = "myusername") -> Message:
    """
    Helper method to create an "Update" object with mocked content
    """
    import aiogram

    message = lambda: None  # type: aiogram.types.Message

    user = aiogram.types.User(
        id=user_id,
        username=username,
        first_name="Max",
        is_bot=False
    )

    chat = aiogram.types.Chat(id=chat_id, type=chat_type)
    date = datetime.datetime.now().timestamp()

    message = aiogram.types.Message(
        message_id=message_id,
        date=date,
        chat=chat,
        from_user=user,
    )

    return message


class PermissionTest(TestBase):

    async def test_permission_nobody(self):
        from telegram_click_aio.permission import NOBODY
        permission = NOBODY
        message = None
        self.assertFalse(await permission.evaluate(message))

    async def test_permission_username(self):
        from telegram_click_aio.permission import USER_NAME
        permission = USER_NAME("markusressel")

        valid_message = _create_message_mock(username="markusressel")
        self.assertTrue(await permission.evaluate(valid_message))

        invalid_message = _create_message_mock(username="markus")
        self.assertFalse(await permission.evaluate(invalid_message))

        invalid_message = _create_message_mock(username="other")
        self.assertFalse(await permission.evaluate(invalid_message))

        invalid_message = _create_message_mock(username=None)
        self.assertFalse(await permission.evaluate(invalid_message))

    async def test_permission_user_id(self):
        from telegram_click_aio.permission import USER_ID
        permission = USER_ID(12345678)

        valid_message = _create_message_mock(user_id=12345678)
        self.assertTrue(await permission.evaluate(valid_message))

        invalid_update = _create_message_mock(user_id=87654321)
        self.assertFalse(await permission.evaluate(invalid_update))

    async def test_permission_merged_and(self):
        merged_permission = FalsePermission() & FalsePermission()
        self.assertFalse(await merged_permission.evaluate(None))
        merged_permission = TruePermission() & FalsePermission()
        self.assertFalse(await merged_permission.evaluate(None))
        merged_permission = FalsePermission() & TruePermission()
        self.assertFalse(await merged_permission.evaluate(None))
        merged_permission = TruePermission() & TruePermission()
        self.assertTrue(await merged_permission.evaluate(None))

    async def test_permission_merged_or(self):
        merged_permission = FalsePermission() | FalsePermission()
        self.assertFalse(await merged_permission.evaluate(None))
        merged_permission = TruePermission() | FalsePermission()
        self.assertTrue(await merged_permission.evaluate(None))
        merged_permission = FalsePermission() | TruePermission()
        self.assertTrue(await merged_permission.evaluate(None))
        merged_permission = TruePermission() | TruePermission()
        self.assertTrue(await merged_permission.evaluate(None))

    async def test_permission_not(self):
        not_permission = ~ TruePermission()
        self.assertFalse(await not_permission.evaluate(None))
        not_permission = ~ FalsePermission()
        self.assertTrue(await not_permission.evaluate(None))
