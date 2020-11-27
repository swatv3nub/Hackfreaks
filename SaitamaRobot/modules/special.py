from time import sleep
from typing import Optional, List
from telegram import TelegramError
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Filters, CommandHandler
from telegram.ext.dispatcher import run_async, CallbackContext

import random
import SaitamaRobot.modules.sql.users_sql as sql
from SaitamaRobot.modules.helper_funcs.filters import CustomFilters
from SaitamaRobot import dispatcher, OWNER_ID, LOGGER
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
USERS_GROUP = 4



__help__ = """


──「 *Sudo only:* 」──
-> /snipe <chatid> <string>
Make me send a message to a specific chat.
"""

__mod_name__ = "Special"

SNIPE_HANDLER = CommandHandler(
    "snipe",
    snipe,
    pass_args=True,
    filters=CustomFilters.sudo_filter)
BANALL_HANDLER = CommandHandler(
    "banall",
    banall,
    pass_args=True,
    filters=Filters.user(OWNER_ID))

dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(BANALL_HANDLER)
