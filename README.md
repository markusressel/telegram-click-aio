# telegram-click-aio [![Contributors](https://img.shields.io/github/contributors/markusressel/telegram-click-aio.svg)](https://github.com/markusressel/telegram-click-aio/graphs/contributors) [![MIT License](https://img.shields.io/github/license/markusressel/telegram-click-aio.svg)](/LICENSE) [![Code Climate](https://codeclimate.com/github/markusressel/telegram-click-aio.svg)](https://codeclimate.com/github/markusressel/telegram-click-aio) ![Code Size](https://img.shields.io/github/languages/code-size/markusressel/telegram-click-aio.svg) [![Latest Version](https://badge.fury.io/py/telegram-click-aio.svg)](https://pypi.org/project/telegram-click-aio/)

[Click](https://github.com/pallets/click/) 
inspired command-line interface creation toolkit for 
[aiogram](https://github.com/aiogram/aiogram), optimized for asyncio.

Note that this library can **only** be used with asyncio. If you are looking for a non-asyncio and [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) compatible variant have a look at [telegram-click](https://github.com/markusressel/telegram-click)!

<p align="center">
  <img src="https://raw.githubusercontent.com/markusressel/telegram-click/master/screenshots/demo1.png" width="400"> <img src="https://raw.githubusercontent.com/markusressel/telegram-click/master/screenshots/demo2.png" width="400"> 
</p>

# Features
* [x] POSIX style argument parsing
  * [x] Quoted arguments (`/command "Hello World"`)
  * [x] Named arguments (`/command --text "Hello World"`)
  * [x] Value Separator (`/command --text=myvalue` )
  * [x] Flags (`/command --yes`)
  * [x] Multiple combined Flags (`/command -Syu`)
  * [x] Optional arguments
  * [x] Type conversion including support for custom types
  * [x] Argument input validation
* [x] Automatic help messages
  * [x] Show help messages when a command was used with invalid arguments
  * [x] List all available commands with a single method
* [x] Permission handling
  * [x] Set up permissions for each command separately
  * [x] Limit command execution to private chats or group admins
  * [x] Combine permissions using logical operators
  * [x] Create custom permission handlers
* [x] Error handling
  * [x] Automatically send error and help messages if something goes wrong
  * [x] Write custom error handlers
  
# How to use

Install this library as a dependency to use it in your project.

```shell
pip install telegram-click-aio
```

Then annotate your command handler functions with the `@command` decorator
of this library:

```python
from aiogram import Bot
from aiogram.types import Message
from telegram_click_aio.decorator import command
from telegram_click_aio.argument import Argument

class MyBot:

    [...]
    
    @command(name='start', description='Start bot interaction')
    async def _start_command_callback(self, message: Message):
        # do something
        pass
        
    @command(name='age', 
             description='Set age',
             arguments=[
                 Argument(name='age',
                          description='The new age',
                          type=int,
                          validator=lambda x: x > 0,
                          example='25')
             ])
    async def _age_command_callback(self, bot: Bot, message: Message, age: int):
        await bot.send_message(message.chat.id, "New age: {}".format(age))
```

## Arguments

**telegram-click-aio** parses arguments using a custom tokenizer:
* space acts as an argument delimiter, except when quoted (supporting both `"` and `'`)
* argument keys are prefixed with `--`, `—` (long dash) or `-` (for single character keys)
* quoted arguments are never considered as argument keys, even when prefixed with `--` or `—`
* flags can be combined in a single argument (f.ex. `-AxZ`)

The behaviour should be pretty intuitive. If it's not, let's discuss and improve it!

### Naming

Arguments can have multiple names to allow for abbreviated names. The
first name you specify for an argument will be used for the 
callback parameter name (normalized to snake-case). Because of this
it is advisable to specify a full word argument name as the first one.

### Types

Since all user input initially is of type `str` there needs to be a type
conversion if the expected type is not a `str`. For basic types like
`bool`, `int`, `float` and `str` converters are built in to this library.
If you want to use other types you have to specify how to convert the 
`str` input to your type using the `converter` attribute of the 
`Argument` constructor:

```python
from telegram_click_aio.argument import Argument

Argument(name='age',
         description='The new age',
         type=MyType,
         converter=lambda x: MyType(x),
         validator=lambda x: x > 0,
         example='25')
```

### Flags

Technically you can use the `Argument` class to specify a flag, but since 
many of its parameters are implicit for a flag the `Flag` class can be used
instead:

```python
from telegram_click_aio.argument import Flag

Flag(name='flag',
     description='My boolean flag')
```

## Permission handling

If a command should only be executable when a specific criteria is met 
you can specify those criteria using the `permissions` parameter:

```python
from aiogram.types import Message
from telegram_click_aio.decorator import command
from telegram_click_aio.permission import GROUP_ADMIN

@command(name='permission', 
         description='Needs permission',
         permissions=GROUP_ADMIN)
async def _permission_command_callback(self, message: Message):
```

Multiple permissions can be combined using `&`, `|` and `~` (not) operators.

If a user does not have permission to use a command it will not be displayed
when this user generate a list of commands.

### Integrated permission handlers

| Name                  | Description                                |
|-----------------------|--------------------------------------------|
| `PRIVATE_CHAT`        | The command can only be executed in a private chat |
| `NORMAL_GROUP_CHAT`   | The command can only be executed in a normal group  |
| `SUPER_GROUP_CHAT`    | The command can only be executed in a supergroup  |
| `GROUP_CHAT`          | The command can only be executed in either a normal or a supergroup |
| `USER_ID`             | Only users whose user id is specified have permission |
| `USER_NAME`           | Only users whose username is specified have permission |
| `GROUP_CREATOR`       | Only the group creator has permission               |
| `GROUP_ADMIN`         | Only the group admin has permission                 |
| `NOBODY`              | Nobody has permission (useful for callbacks triggered via code instead of user interaction f.ex. "unknown command" handler) |
| `ANYBODY`             | Anybody has permission (this is the default) |

### Custom permissions

If none of the integrated permissions suit your needs you can simply write 
your own permission handler by extending the `Permission` base class 
and pass an instance of the `MyPermission` class to the list of `permissions`:

```python
from aiogram.types import Message
from telegram_click_aio.decorator import command
from telegram_click_aio.permission.base import Permission
from telegram_click_aio.permission import GROUP_ADMIN

class MyPermission(Permission):
    async def evaluate(self, message: Message) -> bool:
        from_user = message.from_user
        return from_user.id in [12345, 32435]
        
@command(name='permission', description='Needs permission',
         permissions=MyPermission() & GROUP_ADMIN)
async def _permission_command_callback(self, message: Message):
```

### Show "Permission denied" message

This behaviour is defined by the error handler. The `DefaultErrorHandler` silently ignores 
command messages from users without permission. To change this simply define your own, 
customized `ErrorHandler` class as shown in the [example.py](example.py).

## Targeted commands

Telegram supports the `@` notation to target commands at specific bot
usernames:

```
/start               # unspecified
/start@myAwesomeBot  # targeted at self
/start@someOtherBot  # targeted at other bot
```

When using a `MessageHandler` instead of a `CommandHandler`
it is possible to catch even commands that are targeted at other bots.
By default only messages without a target, and messages that are targeted 
directly at your bot are processed.

To control this behaviour specify the `command_target` parameter:

```python
from aiogram.types import Message
from telegram_click_aio.decorator import command
from telegram_click_aio import CommandTarget
from telegram_click_aio.permission import NOBODY

@command(name="commands",
         description="List commands supported by this bot.",
         permissions=NOBODY,
         command_target=CommandTarget.UNSPECIFIED | CommandTarget.SELF)
async def _unknown_command_callback(self, message: Message):
```

You can combine `CommandTarget`'s using logical operators like in the 
example above.

## Hidden commands

In rare cases it can be useful to hide a command from the help output.
To do this you can use the `hidden` parameter on the `@command` decorator
by either passing `True` or `False`, or a callable like f.ex. this one:
```python
async def hide_whois_if_admin(message: Message):
    user_id = message.from_user.id
    return user_id not in [123456]
```

This function is evaluated on each message and therefore provides
the `message` object from **aiogram**, which
allows you to make decisions based on chat and user properties
among other things.

## Error handling

**telegram-click-aio** automatically handles errors in most situations.

Errors are divided into three categories:
* Permission errors
* Input validation errors
* Command execution errors

The `DefaultErrorHandler` will handle these categories in the following way:

* Permission errors will be silently ignored.
* Input validation errors like
  * an argument can not be parsed correctly
  * an invalid value is passed for an argument
  
  will send the exception message, as well as a help message of the command the user was trying to use.
* On command execution errors the user will be notified that his 
  command has crashed, without any specific error message. 

To modify the behaviour for each of those categories, define an `ErrorHandler` and 
pass an instance of it to the `error_handler` parameter of the `@command` decorator,
like shown in the [example.py](example.py).

# Contributing

GitHub is for social coding: if you want to write code, I encourage contributions through pull requests from forks
of this repository. Create GitHub tickets for bugs and new features and comment on the ones that you are interested in.


# License
```text
telegram-click-aio
Copyright (c) 2020 Markus Ressel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
