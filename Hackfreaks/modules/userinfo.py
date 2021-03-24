import html
import re
import os
import requests
import subprocess
import datetime

from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon import events

from telegram import MAX_MESSAGE_LENGTH, ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext.dispatcher import run_async
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_html

from Hackfreaks import (DEV_USERS, OWNER_ID, DRAGONS, DEMONS, TIGERS, WOLVES,
                          INFOPIC, dispatcher, sw)
from Hackfreaks.__main__ import STATS, TOKEN, USER_INFO
import Hackfreaks.modules.sql.userinfo_sql as sql
from Hackfreaks.modules.disable import DisableAbleCommandHandler
from Hackfreaks.modules.sql.global_bans_sql import is_user_gbanned
from Hackfreaks.modules.sql.afk_sql import is_afk, check_afk_status
from Hackfreaks.modules.sql.users_sql import get_user_num_chats
from Hackfreaks.modules.helper_funcs.chat_status import sudo_plus
from Hackfreaks.modules.helper_funcs.extraction import extract_user
from Hackfreaks import telethn as HackfreaksTelethonClient, TIGERS, DRAGONS, DEMONS
from telegram import __version__
from psutil import cpu_percent, virtual_memory, disk_usage, boot_time
import platform
from platform import python_version

from spamprotection.sync import SPBClient
from spamprotection.errors import HostDownError

client = SPBClient()


@run_async
def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"<b>Telegram ID:</b>,"
                f"• {html.escape(user2.first_name)} - <code>{user2.id}</code>.\n"
                f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(
                f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML)

    else:

        if chat.type == "private":
            msg.reply_text(
                f"Your id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                f"This group's id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)


@HackfreaksTelethonClient.on(
    events.NewMessage(
        pattern='/ginfo ',
        from_users=(TIGERS or []) + (DRAGONS or []) + (DEMONS or [])))
async def group_info(event) -> None:
    chat = event.text.split(' ', 1)[1]
    try:
        entity = await event.client.get_entity(chat)
        totallist = await event.client.get_participants(
            entity, filter=ChannelParticipantsAdmins)
        ch_full = await event.client(GetFullChannelRequest(channel=entity))
    except:
        await event.reply(
            "Can't for some reason, maybe it is a private one or that I am banned there."
        )
        return
    msg = f"**ID**: `{entity.id}`"
    msg += f"\n**Title**: `{entity.title}`"
    msg += f"\n**Datacenter**: `{entity.photo.dc_id}`"
    msg += f"\n**Video PFP**: `{entity.photo.has_video}`"
    msg += f"\n**Supergroup**: `{entity.megagroup}`"
    msg += f"\n**Restricted**: `{entity.restricted}`"
    msg += f"\n**Scam**: `{entity.scam}`"
    msg += f"\n**Slowmode**: `{entity.slowmode_enabled}`"
    if entity.username:
        msg += f"\n**Username**: {entity.username}"
    msg += "\n\n**Member Stats:**"
    msg += f"\n`Admins:` `{len(totallist)}`"
    msg += f"\n`Users`: `{totallist.total}`"
    msg += "\n\n**Admins List:**"
    for x in totallist:
        msg += f"\n• [{x.id}](tg://user?id={x.id})"
    msg += f"\n\n**Description**:\n`{ch_full.full_chat.about}`"
    await event.reply(msg)


@run_async
def gifid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(
            "Please reply to a gif to get its ID.")


@run_async
def info(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    text = (
        f"<b>General:</b>\n"
        f"ID: <code>{user.id}</code>\n"
        f"First Name: {html.escape(user.first_name)}"
    )

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nPermanent user link: {mention_html(user.id, 'link')}"

    try:
        spamwtc = sw.get_ban(int(user.id))
        if spamwtc:
            text += "<b>\n\nSpamWatch:\n</b>"
            text += "<b>This person is banned in Spamwatch!</b>"
            text += f"\nReason: <pre>{spamwtc.reason}</pre>"
            text += "\nAppeal at @SpamWatchSupport"
        else:
            text += "<b>\n\nSpamWatch:</b>\n Not banned"
    except:
        pass  # don't crash if api is down somehow...

    try:
        status = client.raw_output(int(user.id))
        ptid = status["results"]["private_telegram_id"]
        op = status["results"]["attributes"]["is_operator"]
        ag = status["results"]["attributes"]["is_agent"]
        wl = status["results"]["attributes"]["is_whitelisted"]
        ps = status["results"]["attributes"]["is_potential_spammer"]
        sp = status["results"]["spam_prediction"]["spam_prediction"]
        hamp = status["results"]["spam_prediction"]["ham_prediction"]
        blc = status["results"]["attributes"]["is_blacklisted"]
        if blc:
            blres = status["results"]["attributes"]["blacklist_reason"]
        else:
            blres = None
        text += "\n\n<b>SpamProtection:</b>"
        text += f"<b>\nPrivate Telegram ID:</b> <code>{ptid}</code>\n"
        text += f"<b>Operator:</b> <code>{op}</code>\n"
        text += f"<b>Agent:</b> <code>{ag}</code>\n"
        text += f"<b>Whitelisted:</b> <code>{wl}</code>\n"
        text += f"<b>Spam Prediction:</b> <code>{sp}</code>\n"
        text += f"<b>Ham Prediction:</b> <code>{hamp}</code>\n"
        text += f"<b>Potential Spammer:</b> <code>{ps}</code>\n"
        text += f"<b>Blacklisted:</b> <code>{blc}</code>\n"
        text += f"<b>Blacklist Reason:</b> <code>{blres}</code>\n"
    except HostDownError:
        text += "\n\n<b>SpamProtection:</b>"
        text += "\nCan't connect to Intellivoid SpamProtection API\n"

    disaster_level_present = False

    num_chats = get_user_num_chats(user.id)
    text += f"\nChat count: <code>{num_chats}</code>"

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == "administrator":
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result["custom_title"]
                text += f"\nThis user holds the title <b>{custom_title}</b> here."
    except BadRequest:
        pass


    if user.id == OWNER_ID:
        text += f"\nThis person is my owner"
        disaster_level_present = True
    elif user.id in DEV_USERS:
        text += f"\nThis Person is a part of my Devs"
        disaster_level_present = True
    elif user.id in DRAGONS:
        text += f"\nThis Person is an Elite"
        disaster_level_present = True
    elif user.id in DEMONS:
        text += f"\nThis Person is a Knight"
        disaster_level_present = True
    elif user.id in WOLVES:
        text += f"\nThis person is a Horsemen"
        disaster_level_present = True
    elif user.id in TIGERS:
        text += f"\nThis Person is a Goblin"
        disaster_level_present = True

    if disaster_level_present:
        text += ' [<a href="https://t.me/{}?start=nations">?</a>]'.format(bot.username)

    text += "\n"
    for mod in USER_INFO:
        if mod.__mod_name__ == "Users":
            continue

        try:
            mod_info = mod.__user_info__(user.id)
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id)
        if mod_info:
            text += "\n" + mod_info

    if INFOPIC:
        try:
            profile = context.bot.get_user_profile_photos(user.id).photos[0][-1]
            _file = bot.get_file(profile["file_id"])
            _file.download(f"{user.id}.png")

            message.reply_document(
                document=open(f"{user.id}.png", "rb"),
                caption=(text),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)

            os.remove(f"{user.id}.png")
        # Incase user don't have profile pic, send normal text
        except IndexError:
            message.reply_text(
                text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    else:
        message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    rep.delete()


@run_async
def about_me(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(
            f"{username} hasn't set an info message about themselves yet!")
    else:
        update.effective_message.reply_text(
            "There isnt one, use /setme to set one.")


@run_async
def set_about_me(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = message.from_user.id
    if user_id in [777000, 1087968824]:
        message.reply_text("Error! Unauthorized")
        return
    bot = context.bot
    if message.reply_to_message:
        repl_message = message.reply_to_message
        repl_user_id = repl_message.from_user.id
        if repl_user_id in [bot.id, 777000, 1087968824] and (user_id
                                                             in DEV_USERS):
            user_id = repl_user_id
    text = message.text
    info = text.split(None, 1)
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            if user_id in [777000, 1087968824]:
                message.reply_text("Authorized...Information updated!")
            elif user_id == bot.id:
                message.reply_text(
                    "I have updated my info with the one you provided!")
            else:
                message.reply_text("Information updated!")
        else:
            message.reply_text(
                "The info needs to be under {} characters! You have {}.".format(
                    MAX_MESSAGE_LENGTH // 4, len(info[1])))


@run_async
@sudo_plus
def stats(update, context):
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    status = "*>-------< System >-------<*\n"
    status += "*System uptime:* " + str(uptime) + "\n"

    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    status += "*CPU usage:* " + str(cpu) + " %\n"
    status += "*Ram usage:* " + str(mem[2]) + " %\n"
    status += "*Storage used:* " + str(disk[3]) + " %\n\n"
    status += "*Python version:* " + python_version() + "\n"
    status += "*Library version:* " + str(__version__) + "\n"
    try:
        update.effective_message.reply_text(

            f"*[Hackfreaks](t.me/MrHackfreaksRobot), *\n" +
            "Maintained by [🇮🇳 スウォニット](t.me/MaskedVirus)\n" +
            "Library used : python-telegram-bot\n\n" + status +
            "\n*Bot statistics*:\n"
            + "\n".join([mod.__stats__() for mod in STATS]) +
            "\n\n*Source*: [GitHub](https://github.com/swatv3nub/Hackfreaks)",
        parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    except BaseException:
        update.effective_message.reply_text(

            f"*Hackfreaks (@{context.bot.username}), *\n" +
            "Maintained by [🇮🇳 スウォニット](t.me/MaskedVirus)\n" +
            "Library used : python-telegram-bot\n" +
            "\n*Bot statistics*:\n"
            + "\n".join([mod.__stats__() for mod in STATS]) +
            "\n\n*[GitHub](https://github.com/swatv3nub/Hackfreaks)",
        parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


@run_async
def about_bio(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text(
            "*{}*:\n{}".format(user.first_name, escape_markdown(info)),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text(
            f"{username} hasn't had a message set about themselves yet!\nSet one using /setbio"
        )
    else:
        update.effective_message.reply_text(
            "You haven't had a bio set about yourself yet!")


@run_async
def set_about_bio(update: Update, context: CallbackContext):
    message = update.effective_message
    sender_id = update.effective_user.id
    bot = context.bot

    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id

        if user_id == message.from_user.id:
            message.reply_text(
                "Ha, you can't set your own bio! You're at the mercy of others here..."
            )
            return

        if user_id in [777000, 1087968824] and sender_id not in DEV_USERS:
            message.reply_text("You are not authorised")
            return

        if user_id == bot.id and sender_id not in DEV_USERS:
            message.reply_text(
                "Erm... yeah, I only trust my EMPEROR to set my bio.")
            return

        text = message.text
        bio = text.split(
            None, 1
        )  # use python's maxsplit to only remove the cmd, hence keeping newlines.

        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("Updated {}'s bio!".format(
                    repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "Bio needs to be under {} characters! You tried to set {}."
                    .format(MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text("Reply to someone to set their bio!")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    result = ""
    if me:
        result += f"<b>About user:</b>\n{me}\n"
    if bio:
        result += f"<b>What others say:</b>\n{bio}\n"
    result = result.strip("\n")
    return result


__help__ = """
*ID:*
 • `/id`*:* get the current group id. If used by replying to a message, gets that user's id.
 • `/gifid`*:* reply to a gif to me to tell you its file ID.

*Self addded information:* 
 • `/setme <text>`*:* will set your info
 • `/me`*:* will get your or another user's info.
Examples:
 `/setme I am a wolf.`
 `/me @username(defaults to yours if no user specified)`

*Information others add on you:* 
 • `/bio`*:* will get your or another user's bio. This cannot be set by yourself.
• `/setbio <text>`*:* while replying, will save another user's bio 
Examples:
 `/bio @username(defaults to yours if not specified).`
 `/setbio This user is a wolf` (reply to the user)

*Overall Information about you:*
 • `/info`*:* get information about a user. 
 
*What is that health thingy?*
 Come and see [HP System explained](https://t.me/HackfreaksUpdates/8)
"""

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio)

STATS_HANDLER = CommandHandler("stats", stats)
ID_HANDLER = DisableAbleCommandHandler("id", get_id)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid)
INFO_HANDLER = DisableAbleCommandHandler(("info", "book"), info)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me)

dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(GIFID_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)

__mod_name__ = "Info"
__command_list__ = ["setbio", "bio", "setme", "me", "info"]
__handlers__ = [
    ID_HANDLER, GIFID_HANDLER, INFO_HANDLER, SET_BIO_HANDLER, GET_BIO_HANDLER,
    SET_ABOUT_HANDLER, GET_ABOUT_HANDLER, STATS_HANDLER
]
