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

from telegram_click_aio.permission.chat import _PrivateChat, _GroupChat, _SuperGroupChat
from telegram_click_aio.permission.user import _GroupCreator, _GroupAdmin, _UserId, _UserName, _Nobody, _Anybody

PRIVATE_CHAT = _PrivateChat()
NORMAL_GROUP_CHAT = _GroupChat()
SUPER_GROUP_CHAT = _SuperGroupChat()
GROUP_CHAT = NORMAL_GROUP_CHAT | SUPER_GROUP_CHAT

ANYBODY = _Anybody()
NOBODY = _Nobody()
USER_ID = _UserId
USER_NAME = _UserName
GROUP_CREATOR = (_GroupCreator() & GROUP_CHAT)
GROUP_ADMIN = (_GroupAdmin() & GROUP_CHAT)
