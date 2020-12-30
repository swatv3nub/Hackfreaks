import csv
import json
import os
import re
import time
import uuid
from io import BytesIO
import html

import Hackfreaks.modules.sql.dynasty_sql as sql
from Hackfreaks import (EVENT_LOGS, LOGGER, OWNER_ID, DRAGONS, TIGERS, WOLVES,
                          dispatcher)
from Hackfreaks.modules.disable import DisableAbleCommandHandler
from Hackfreaks.modules.helper_funcs.alternate import send_message
from Hackfreaks.modules.helper_funcs.chat_status import is_user_admin
from Hackfreaks.modules.helper_funcs.extraction import (extract_unt_dynastyban,
                                                          extract_user,
                                                          extract_user_dban)
from Hackfreaks.modules.helper_funcs.string_handling import markdown_parser
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity,
                      ParseMode, Update)
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          run_async)
from telegram.utils.helpers import (mention_html, mention_markdown)

# Hello bot owner, I spended for Dynasties many hours of my life, Please don't remove this if you still respect MrYacha and peaktogoo and AyraHikari too
# Dynasty by MrYacha 2018-2019
# Dynasty rework by Mizukito Akito 2019
# Dynasty update v2 by Ayra Hikari 2019
# Time spent on dynasties = 10h by #MrYacha
# Time spent on reworking on the whole dynasties = 22h+ by @peaktogoo
# Time spent on updating version to v2 = 26h+ by @AyraHikari
# Time Spent on renaming Dynastys to Dynasty, Changing Commands, adding New Handlers = 1.5h+ by @TheFuckErGuy
# Total spended for making this features is 69h+
# LOGGER.info("Original Dynasty module by MrYacha, reworked by Mizukito Akito (@peaktogoo) on Telegram.")
# Here DYNASTY means FEDERATIONS. MrYatcha, Ayra Hikari, peaktogoo actually made the Federations, I just Renamed, changed commands, SQLs etc.

DBAN_ERRORS = {
    "User is an administrator of the chat", "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant", "Peer_id_invalid", "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private", "Not in the chat", "Have no rights to send a message"
}

UNDBAN_ERRORS = {
    "User is an administrator of the chat", "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat", "Channel_private", "Chat_admin_required",
    "Have no rights to send a message"
}


@run_async
def new_dynasty(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if chat.type != "private":
        update.effective_message.reply_text(
            "Dynasty can only be created by privately messaging me.")
        return
    if len(message.text) == 1:
        send_message(update.effective_message,
                     "Please write the name of the Dynasty!")
        return
    dynastynam = message.text.split(None, 1)[1]
    if not dynastynam == '':
        dynasty_id = str(uuid.uuid4())
        dynasty_name = dynastynam
        LOGGER.info(dynasty_id)

        x = sql.new_dynasty(user.id, dynasty_name, dynasty_id)
        if not x:
            update.effective_message.reply_text(
                "Can't dynastyerate! Please contact @HackfreaksSupport if the problem persist."
            )
            return

        update.effective_message.reply_text("*You have succeeded in creating a new Dynasty!*"\
                 "\nName: `{}`"\
                 "\nID: `{}`"
                 "\n\nUse the command below to join the Dynasty:"
                 "\n`/joindynasty {}`".format(dynasty_name, dynasty_id, dynasty_id), parse_mode=ParseMode.MARKDOWN)
        try:
            bot.send_message(
                EVENT_LOGS,
                "New Dynasty: <b>{}</b>\nID: <pre>{}</pre>".format(
                    dynasty_name, dynasty_id),
                parse_mode=ParseMode.HTML)
        except:
            LOGGER.warning("Cannot send a message to EVENT_LOGS")
    else:
        update.effective_message.reply_text(
            "Please write down the name of the Dynasty")


@run_async
def del_dynasty(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    if chat.type != "private":
        update.effective_message.reply_text(
            "Dynasty can only be deleted by privately messaging me.")
        return
    if args:
        is_dynasty_id = args[0]
        getinfo = sql.get_dynasty_info(is_dynasty_id)
        if getinfo is False:
            update.effective_message.reply_text(
                "This Dynasty does not exist.")
            return
        if int(getinfo['owner']) == int(user.id) or int(user.id) == OWNER_ID:
            dynasty_id = is_dynasty_id
        else:
            update.effective_message.reply_text(
                "Only Dynasty owners can do this!")
            return
    else:
        update.effective_message.reply_text("What should I delete?")
        return

    if is_user_dynasty_owner(dynasty_id, user.id) is False:
        update.effective_message.reply_text(
            "Only Dynasty owners can do this!")
        return

    update.effective_message.reply_text(
        "You sure you want to delete your Dynasty? This cannot be reverted, you will lose your entire ban list, and '{}' will be permanently lost."
        .format(getinfo['dname']),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="⚠️ Delete Dynasty ⚠️",
                callback_data="rmdynasty_{}".format(dynasty_id))
        ], [InlineKeyboardButton(text="Cancel",
                                 callback_data="rmdynasty_cancel")]]))


@run_async
def rename_dynasty(update, context):
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(None, 2)

    if len(args) < 3:
        return msg.reply_text("usage: /renamedynasty <dynasty_id> <newname>")

    dynasty_id, newname = args[1], args[2]
    verify_dynasty = sql.get_dynasty_info(dynasty_id)

    if not verify_dynasty:
        return msg.reply_text("This dynasty not exist in my database!")

    if is_user_dynasty_owner(dynasty_id, user.id):
        sql.rename_dynasty(dynasty_id, user.id, newname)
        msg.reply_text(f"Successfully renamed your dynasty name to {newname}!")
    else:
        msg.reply_text("Only Dynasty owner can do this!")


@run_async
def dynasty_chat(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    dynasty_id = sql.get_dynasty_id(chat.id)

    user_id = update.effective_message.from_user.id
    if not is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(
            "You must be an admin to execute this command")
        return

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not in any Dynasty!")
        return

    user = update.effective_user
    chat = update.effective_chat
    info = sql.get_dynasty_info(dynasty_id)

    text = "This group is part of the following Dynasty:"
    text += "\n{} (ID: <code>{}</code>)".format(info['dname'], dynasty_id)

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def join_dynasty(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    message = update.effective_message
    administrators = chat.get_administrators()
    dynasty_id = sql.get_dynasty_id(chat.id)

    if user.id in DRAGONS:
        pass
    else:
        for admin in administrators:
            status = admin.status
            if status == "creator":
                if str(admin.user.id) == str(user.id):
                    pass
                else:
                    update.effective_message.reply_text(
                        "Only group creators can use this command!")
                    return
    if dynasty_id:
        message.reply_text("You cannot join two Dynasty from one chat")
        return

    if len(args) >= 1:
        getdynasty = sql.search_dynasty_by_id(args[0])
        if getdynasty is False:
            message.reply_text("Please enter a valid Dynasty ID")
            return

        x = sql.chat_join_dynasty(args[0], chat.title, chat.id)
        if not x:
            message.reply_text(
                "Failed to join Dynasty! Please contact @HackfreaksSupport should this problem persist!"
            )
            return

        get_dynastylog = sql.get_dynasty_log(args[0])
        if get_dynastylog:
            if eval(get_dynastylog):
                bot.send_message(
                    get_dynastylog,
                    "Chat *{}* has joined the Dynasty *{}*".format(
                        chat.title, getdynasty['dname']),
                    parse_mode="markdown")

        message.reply_text("This group has joined the Dynasty: {}!".format(
            getdynasty['dname']))


@run_async
def leave_dynasty(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our PM!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)
    dynasty_info = sql.get_dynasty_info(dynasty_id)

    # administrators = chat.get_administrators().status
    getuser = bot.get_chat_member(chat.id, user.id).status
    if getuser in 'creator' or user.id in DRAGONS:
        if sql.chat_leave_dynasty(chat.id) is True:
            get_dynastylog = sql.get_dynasty_log(dynasty_id)
            if get_dynastylog:
                if eval(get_dynastylog):
                    bot.send_message(
                        get_dynastylog,
                        "Chat *{}* has left the Dynasty *{}*".format(
                            chat.title, dynasty_info['dname']),
                        parse_mode="markdown")
            send_message(
                update.effective_message,
                "This group has left the Dynasty {}!".format(
                    dynasty_info['dname']))
        else:
            update.effective_message.reply_text(
                "How can you leave a Dynasty that you never joined?!")
    else:
        update.effective_message.reply_text(
            "Only group creators can use this command!")


@run_async
def user_join_dynasty(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)

    if is_user_dynasty_owner(dynasty_id, user.id) or user.id in DRAGONS:
        user_id = extract_user(msg, args)
        if user_id:
            user = bot.get_chat(user_id)
        elif not msg.reply_to_message and not args:
            user = msg.from_user
        elif not msg.reply_to_message and (
                not args or
            (len(args) >= 1 and not args[0].startswith("@") and
             not args[0].isdigit() and
             not msg.parse_entities([MessageEntity.TEXT_MENTION]))):
            msg.reply_text("I cannot extract user from this message")
            return
        else:
            LOGGER.warning('error')
        getuser = sql.search_user_in_dynasty(dynasty_id, user_id)
        dynasty_id = sql.get_dynasty_id(chat.id)
        info = sql.get_dynasty_info(dynasty_id)
        get_owner = eval(info['dusers'])['owner']
        get_owner = bot.get_chat(get_owner).id
        if user_id == get_owner:
            update.effective_message.reply_text(
                "You do know that the user is the Dynasty owner, right? RIGHT?"
            )
            return
        if getuser:
            update.effective_message.reply_text(
                "I cannot promote users who are already Dynasty admins! Can remove them if you want!"
            )
            return
        if user_id == bot.id:
            update.effective_message.reply_text(
                "I already am a Dynasty admin in all Dynasty!")
            return
        res = sql.user_join_dynasty(dynasty_id, user_id)
        if res:
            update.effective_message.reply_text("Successfully Promoted!")
        else:
            update.effective_message.reply_text("Failed to promote!")
    else:
        update.effective_message.reply_text(
            "Only Dynasty owners can do this!")


@run_async
def user_demote_dynasty(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)

    if is_user_dynasty_owner(dynasty_id, user.id):
        msg = update.effective_message
        user_id = extract_user(msg, args)
        if user_id:
            user = bot.get_chat(user_id)

        elif not msg.reply_to_message and not args:
            user = msg.from_user

        elif not msg.reply_to_message and (
                not args or
            (len(args) >= 1 and not args[0].startswith("@") and
             not args[0].isdigit() and
             not msg.parse_entities([MessageEntity.TEXT_MENTION]))):
            msg.reply_text("I cannot extract user from this message")
            return
        else:
            LOGGER.warning('error')

        if user_id == bot.id:
            update.effective_message.reply_text(
                "The thing you are trying to demote me from will fail to work without me! Just saying."
            )
            return

        if sql.search_user_in_dynasty(dynasty_id, user_id) is False:
            update.effective_message.reply_text(
                "I cannot demote people who are not Dynasty admins!")
            return

        res = sql.user_demote_dynasty(dynasty_id, user_id)
        if res is True:
            update.effective_message.reply_text("Demoted from a Dynasty Admin!")
        else:
            update.effective_message.reply_text("Demotion failed!")
    else:
        update.effective_message.reply_text(
            "Only Dynasty owners can do this!")
        return


@run_async
def dynasty_info(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    if args:
        dynasty_id = args[0]
        info = sql.get_dynasty_info(dynasty_id)
    else:
        dynasty_id = sql.get_dynasty_id(chat.id)
        if not dynasty_id:
            send_message(update.effective_message,
                         "This group is not in any Dynasty!")
            return
        info = sql.get_dynasty_info(dynasty_id)

    if is_user_dynasty_admin(dynasty_id, user.id) is False:
        update.effective_message.reply_text(
            "Only a Dynasty admin can do this!")
        return

    owner = bot.get_chat(info['owner'])
    try:
        owner_name = owner.first_name + " " + owner.last_name
    except:
        owner_name = owner.first_name
    DYNASTYADMIN = sql.all_dynasty_users(dynasty_id)
    TotalAdminDynasty = len(DYNASTYADMIN)

    user = update.effective_user
    chat = update.effective_chat
    info = sql.get_dynasty_info(dynasty_id)

    text = "<b>ℹ️ Dynasty Information:</b>"
    text += "\nDynastyID: <code>{}</code>".format(dynasty_id)
    text += "\nName: {}".format(info['dname'])
    text += "\nCreator: {}".format(mention_html(owner.id, owner_name))
    text += "\nAll Admins: <code>{}</code>".format(TotalAdminDynasty)
    getdban = sql.get_all_dban_users(dynasty_id)
    text += "\nTotal banned users: <code>{}</code>".format(len(getdban))
    getfchat = sql.all_dynasty_chats(dynasty_id)
    text += "\nNumber of groups in this Dynasty: <code>{}</code>".format(
        len(getfchat))

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def dynasty_admin(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not in any Dynasty!")
        return

    if is_user_dynasty_admin(dynasty_id, user.id) is False:
        update.effective_message.reply_text(
            "Only Dynasty admins can do this!")
        return

    user = update.effective_user
    chat = update.effective_chat
    info = sql.get_dynasty_info(dynasty_id)

    text = "<b>Dynasty Admin {}:</b>\n\n".format(info['dname'])
    text += "👑 Owner:\n"
    owner = bot.get_chat(info['owner'])
    try:
        owner_name = owner.first_name + " " + owner.last_name
    except:
        owner_name = owner.first_name
    text += " • {}\n".format(mention_html(owner.id, owner_name))

    members = sql.all_dynasty_members(dynasty_id)
    if len(members) == 0:
        text += "\n🔱 There are no admins in this Dynasty"
    else:
        text += "\n🔱 Admin:\n"
        for x in members:
            user = bot.get_chat(x)
            text += " • {}\n".format(mention_html(user.id, user.first_name))

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def dynasty_ban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not a part of any Dynasty!")
        return

    info = sql.get_dynasty_info(dynasty_id)
    getdynastynotif = sql.user_dynasties_report(info['owner'])

    if is_user_dynasty_admin(dynasty_id, user.id) is False:
        update.effective_message.reply_text(
            "Only Dynasty admins can do this!")
        return

    message = update.effective_message

    user_id, reason = extract_unt_dynastyban(message, args)

    dban, dbanreason, dbantime = sql.get_dban_user(dynasty_id, user_id)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user")
        return

    if user_id == bot.id:
        message.reply_text(
            "What is funnier than kicking the group creator? Self sacrifice.")
        return

    if is_user_dynasty_owner(dynasty_id, user_id) is True:
        message.reply_text("Why did you try the Dynasty dban?")
        return

    if is_user_dynasty_admin(dynasty_id, user_id) is True:
        message.reply_text("He is a Dynasty admin, I can't dban him.")
        return

    if user_id == OWNER_ID:
        message.reply_text("Emperors cannot be dynasty banned!")
        return

    if int(user_id) in DRAGONS:
        message.reply_text("Dragons cannot be dynasty banned!")
        return

    if int(user_id) in TIGERS:
        message.reply_text("Tigers cannot be dynasty banned!")
        return

    if int(user_id) in WOLVES:
        message.reply_text("Wolves cannot be dynasty banned!")
        return

    if user_id in [777000, 1087968824]:
        message.reply_text("Fool! You can't attack Telegram's native tech!")
        return

    try:
        user_chat = bot.get_chat(user_id)
        isvalid = True
        dban_user_id = user_chat.id
        dban_user_name = user_chat.first_name
        dban_user_lname = user_chat.last_name
        dban_user_uname = user_chat.username
    except BadRequest as excp:
        if not str(user_id).isdigit():
            send_message(update.effective_message, excp.message)
            return
        elif len(str(user_id)) != 9:
            send_message(update.effective_message, "That's so not a user!")
            return
        isvalid = False
        dban_user_id = int(user_id)
        dban_user_name = "user({})".format(user_id)
        dban_user_lname = None
        dban_user_uname = None

    if isvalid and user_chat.type != 'private':
        send_message(update.effective_message, "That's so not a user!")
        return

    if isvalid:
        user_target = mention_html(dban_user_id, dban_user_name)
    else:
        user_target = dban_user_name

    if dban:
        dynasty_name = info['dname']
        
        temp = sql.un_dban_user(dynasty_id, dban_user_id)
        if not temp:
            message.reply_text("Failed to update the reason for dynastyban!")
            return
        x = sql.dban_user(dynasty_id, dban_user_id, dban_user_name, dban_user_lname,
                          dban_user_uname, reason, int(time.time()))
        if not x:
            message.reply_text(
                "Failed to ban from the Dynasty! If this problem continues, contact @HackfreaksSupport."
            )
            return

        dynasty_chats = sql.all_dynasty_chats(dynasty_id)
        # Will send to current chat
        bot.send_message(chat.id, "<b>DynastyBan reason updated</b>" \
              "\n<b>Dynasty:</b> {}" \
              "\n<b>Dynasty Admin:</b> {}" \
              "\n<b>User:</b> {}" \
              "\n<b>User ID:</b> <code>{}</code>" \
              "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), parse_mode="HTML")
        # Send message to owner if dynastynotif is enabled
        if getdynastynotif:
            bot.send_message(info['owner'], "<b>DynastyBan reason updated</b>" \
                 "\n<b>Dynasty:</b> {}" \
                 "\n<b>Dynasty Admin:</b> {}" \
                 "\n<b>User:</b> {}" \
                 "\n<b>User ID:</b> <code>{}</code>" \
                 "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), parse_mode="HTML")
        # If dynastylog is set, then send message, except dynastylog is current chat
        get_dynastylog = sql.get_dynasty_log(dynasty_id)
        if get_dynastylog:
            if int(get_dynastylog) != int(chat.id):
                bot.send_message(get_dynastylog, "<b>DynastyBan reason updated</b>" \
                    "\n<b>Dynasty:</b> {}" \
                    "\n<b>Dynasty Admin:</b> {}" \
                    "\n<b>User:</b> {}" \
                    "\n<b>User ID:</b> <code>{}</code>" \
                    "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), parse_mode="HTML")
        for dynastieschat in dynasty_chats:
            try:
                # Do not spam all dynasty chats
                """
				bot.send_message(chat, "<b>DynastyBan reason updated</b>" \
							 "\n<b>Dynasty:</b> {}" \
							 "\n<b>Dynasty Admin:</b> {}" \
							 "\n<b>User:</b> {}" \
							 "\n<b>User ID:</b> <code>{}</code>" \
							 "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), parse_mode="HTML")
				"""
                bot.kick_chat_member(dynastieschat, dban_user_id)
            except BadRequest as excp:
                if excp.message in DBAN_ERRORS:
                    try:
                        dispatcher.bot.getChat(dynastieschat)
                    except Unauthorized:
                        sql.chat_leave_dynasty(dynastieschat)
                        LOGGER.info(
                            "Chat {} has leave dynasty {} because I was kicked"
                            .format(dynastieschat, info['dname']))
                        continue
                elif excp.message == "User_id_invalid":
                    break
                else:
                    LOGGER.warning("Could not dban on {} because: {}".format(
                        chat, excp.message))
            except TelegramError:
                pass
        # Also do not spam all dynasty admins
        """
		send_to_list(bot, DYNASTYADMIN,
				 "<b>DynastyBan reason updated</b>" \
							 "\n<b>Dynasty:</b> {}" \
							 "\n<b>Dynasty Admin:</b> {}" \
							 "\n<b>User:</b> {}" \
							 "\n<b>User ID:</b> <code>{}</code>" \
							 "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), 
							html=True)
		"""

        # DynastyBan for dynasty subscriber
        subscriber = list(sql.get_subscriber(dynasty_id))
        if len(subscriber) != 0:
            for dynastiesid in subscriber:
                all_dynastieschat = sql.all_dynasty_chats(dynastiesid)
                for dynastieschat in all_dynastieschat:
                    try:
                        bot.kick_chat_member(dynastieschat, dban_user_id)
                    except BadRequest as excp:
                        if excp.message in DBAN_ERRORS:
                            try:
                                dispatcher.bot.getChat(dynastieschat)
                            except Unauthorized:
                                targetdynasty_id = sql.get_dynasty_id(dynastieschat)
                                sql.unsubs_dynasty(dynasty_id, targetdynasty_id)
                                LOGGER.info(
                                    "Chat {} has unsub dynasty {} because I was kicked"
                                    .format(dynastieschat, info['dname']))
                                continue
                        elif excp.message == "User_id_invalid":
                            break
                        else:
                            LOGGER.warning(
                                "Unable to dban on {} because: {}".format(
                                    dynastieschat, excp.message))
                    except TelegramError:
                        pass
        #send_message(update.effective_message, "Dynastyban Reason has been updated.")
        return

    dynasty_name = info['dname']

    #starting = "Starting a Dynasty ban for {} in the Dynasty <b>{}</b>.".format(
    #    user_target, dynasty_name)
    #update.effective_message.reply_text(starting, parse_mode=ParseMode.HTML)

    #if reason == "":
    #    reason = "No reason given."

    x = sql.dban_user(dynasty_id, dban_user_id, dban_user_name, dban_user_lname,
                      dban_user_uname, reason, int(time.time()))
    if not x:
        message.reply_text(
            "Failed to ban from the Dynasty! If this problem continues, contact @HackfreaksSupport."
        )
        return

    dynasty_chats = sql.all_dynasty_chats(dynasty_id)
    # Will send to current chat
    bot.send_message(chat.id, "<b>DynastyBan reason updated</b>" \
          "\n<b>Dynasty:</b> {}" \
          "\n<b>Dynasty Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>User ID:</b> <code>{}</code>" \
          "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), parse_mode="HTML")
    # Send message to owner if dynastynotif is enabled
    if getdynastynotif:
        bot.send_message(info['owner'], "<b>DynastyBan reason updated</b>" \
             "\n<b>Dynasty:</b> {}" \
             "\n<b>Dynasty Admin:</b> {}" \
             "\n<b>User:</b> {}" \
             "\n<b>User ID:</b> <code>{}</code>" \
             "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), parse_mode="HTML")
    # If dynastylog is set, then send message, except dynastylog is current chat
    get_dynastylog = sql.get_dynasty_log(dynasty_id)
    if get_dynastylog:
        if int(get_dynastylog) != int(chat.id):
            bot.send_message(get_dynastylog, "<b>DynastyBan reason updated</b>" \
                "\n<b>Dynasty:</b> {}" \
                "\n<b>Dynasty Admin:</b> {}" \
                "\n<b>User:</b> {}" \
                "\n<b>User ID:</b> <code>{}</code>" \
                "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), parse_mode="HTML")
    chats_in_dynasty = 0
    for dynastieschat in dynasty_chats:
        chats_in_dynasty += 1
        try:
            # Do not spamming all dynasty chats
            """
			bot.send_message(chat, "<b>DynastyBan reason updated</b>" \
							"\n<b>Dynasty:</b> {}" \
							"\n<b>Dynasty Admin:</b> {}" \
							"\n<b>User:</b> {}" \
							"\n<b>User ID:</b> <code>{}</code>" \
							"\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), parse_mode="HTML")
			"""
            bot.kick_chat_member(dynastieschat, dban_user_id)
        except BadRequest as excp:
            if excp.message in DBAN_ERRORS:
                pass
            elif excp.message == "User_id_invalid":
                break
            else:
                LOGGER.warning("Could not dban on {} because: {}".format(
                    chat, excp.message))
        except TelegramError:
            pass

    # Also do not spamming all dynasty admins
        """
		send_to_list(bot, DYNASTYADMIN,
				 "<b>DynastyBan reason updated</b>" \
							 "\n<b>Dynasty:</b> {}" \
							 "\n<b>Dynasty Admin:</b> {}" \
							 "\n<b>User:</b> {}" \
							 "\n<b>User ID:</b> <code>{}</code>" \
							 "\n<b>Reason:</b> {}".format(dynasty_name, mention_html(user.id, user.first_name), user_target, dban_user_id, reason), 
							html=True)
		"""

        # DynastyBan for dynasty subscriber
        subscriber = list(sql.get_subscriber(dynasty_id))
        if len(subscriber) != 0:
            for dynastiesid in subscriber:
                all_dynastieschat = sql.all_dynasty_chats(dynastiesid)
                for dynastieschat in all_dynastieschat:
                    try:
                        bot.kick_chat_member(dynastieschat, dban_user_id)
                    except BadRequest as excp:
                        if excp.message in DBAN_ERRORS:
                            try:
                                dispatcher.bot.getChat(dynastieschat)
                            except Unauthorized:
                                targetdynasty_id = sql.get_dynasty_id(dynastieschat)
                                sql.unsubs_dynasty(dynasty_id, targetdynasty_id)
                                LOGGER.info(
                                    "Chat {} has unsub dynasty {} because I was kicked"
                                    .format(dynastieschat, info['dname']))
                                continue
                        elif excp.message == "User_id_invalid":
                            break
                        else:
                            LOGGER.warning(
                                "Unable to dban on {} because: {}".format(
                                    dynastieschat, excp.message))
                    except TelegramError:
                        pass
    #if chats_in_dynasty == 0:
    #    send_message(update.effective_message, "Dynastyban affected 0 chats. ")
    #elif chats_in_dynasty > 0:
    #    send_message(update.effective_message,
    #                 "Dynastyban affected {} chats. ".format(chats_in_dynasty))


@run_async
def undban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not a part of any Dynasty!")
        return

    info = sql.get_dynasty_info(dynasty_id)
    getdynastynotif = sql.user_dynasties_report(info['owner'])

    if is_user_dynasty_admin(dynasty_id, user.id) is False:
        update.effective_message.reply_text(
            "Only Dynasty admins can do this!")
        return

    user_id = extract_user_dban(message, args)
    if not user_id:
        message.reply_text("You do not seem to be referring to a user.")
        return

    try:
        user_chat = bot.get_chat(user_id)
        isvalid = True
        dban_user_id = user_chat.id
        dban_user_name = user_chat.first_name
        dban_user_lname = user_chat.last_name
        dban_user_uname = user_chat.username
    except BadRequest as excp:
        if not str(user_id).isdigit():
            send_message(update.effective_message, excp.message)
            return
        elif len(str(user_id)) != 9:
            send_message(update.effective_message, "That's so not a user!")
            return
        isvalid = False
        dban_user_id = int(user_id)
        dban_user_name = "user({})".format(user_id)
        dban_user_lname = None
        dban_user_uname = None

    if isvalid and user_chat.type != 'private':
        message.reply_text("That's so not a user!")
        return

    if isvalid:
        user_target = mention_html(dban_user_id, dban_user_name)
    else:
        user_target = dban_user_name

    dban, dbanreason, dbantime = sql.get_dban_user(dynasty_id, dban_user_id)
    if dban is False:
        message.reply_text("This user is not dbanned!")
        return

    banner = update.effective_user

    #message.reply_text("I'll give {} another chance in this Dynasty".format(user_chat.first_name))

    chat_list = sql.all_dynasty_chats(dynasty_id)
    # Will send to current chat
    bot.send_message(chat.id, "<b>Un-DynastyBan</b>" \
          "\n<b>Dynasty:</b> {}" \
          "\n<b>Dynasty Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>User ID:</b> <code>{}</code>".format(info['dname'], mention_html(user.id, user.first_name), user_target, dban_user_id), parse_mode="HTML")
    # Send message to owner if dynastynotif is enabled
    if getdynastynotif:
        bot.send_message(info['owner'], "<b>Un-DynastyBan</b>" \
             "\n<b>Dynasty:</b> {}" \
             "\n<b>Dynasty Admin:</b> {}" \
             "\n<b>User:</b> {}" \
             "\n<b>User ID:</b> <code>{}</code>".format(info['dname'], mention_html(user.id, user.first_name), user_target, dban_user_id), parse_mode="HTML")
    # If dynastylog is set, then send message, except dynastylog is current chat
    get_dynastylog = sql.get_dynasty_log(dynasty_id)
    if get_dynastylog:
        if int(get_dynastylog) != int(chat.id):
            bot.send_message(get_dynastylog, "<b>Un-DynastyBan</b>" \
                "\n<b>Dynasty:</b> {}" \
                "\n<b>Dynasty Admin:</b> {}" \
                "\n<b>User:</b> {}" \
                "\n<b>User ID:</b> <code>{}</code>".format(info['dname'], mention_html(user.id, user.first_name), user_target, dban_user_id), parse_mode="HTML")
    undbanned_in_chats = 0
    for dynastychats in chat_list:
        undbanned_in_chats += 1
        try:
            member = bot.get_chat_member(dynastychats, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(dynastychats, user_id)
            # Do not spamming all dynasty chats
            """
			bot.send_message(chat, "<b>Un-DynastyBan</b>" \
						 "\n<b>Dynasty:</b> {}" \
						 "\n<b>Dynasty Admin:</b> {}" \
						 "\n<b>User:</b> {}" \
						 "\n<b>User ID:</b> <code>{}</code>".format(info['dname'], mention_html(user.id, user.first_name), user_target, dban_user_id), parse_mode="HTML")
			"""
        except BadRequest as excp:
            if excp.message in UNDBAN_ERRORS:
                pass
            elif excp.message == "User_id_invalid":
                break
            else:
                LOGGER.warning("Could not dban on {} because: {}".format(
                    chat, excp.message))
        except TelegramError:
            pass

    try:
        x = sql.un_dban_user(dynasty_id, user_id)
        if not x:
            send_message(
                update.effective_message,
                "Un-dban failed, this user may already be un-dynastybanned!")
            return
    except:
        pass

    # UnDynastyBan for dynasty subscriber
    subscriber = list(sql.get_subscriber(dynasty_id))
    if len(subscriber) != 0:
        for dynastiesid in subscriber:
            all_dynastieschat = sql.all_dynasty_chats(dynastiesid)
            for dynastieschat in all_dynastieschat:
                try:
                    bot.unban_chat_member(dynastychats, user_id)
                except BadRequest as excp:
                    if excp.message in DBAN_ERRORS:
                        try:
                            dispatcher.bot.getChat(dynastieschat)
                        except Unauthorized:
                            targetdynasty_id = sql.get_dynasty_id(dynastieschat)
                            sql.unsubs_dynasty(dynasty_id, targetdynasty_id)
                            LOGGER.info(
                                "Chat {} has unsub dynasty {} because I was kicked"
                                .format(dynastieschat, info['dname']))
                            continue
                    elif excp.message == "User_id_invalid":
                        break
                    else:
                        LOGGER.warning(
                            "Unable to dban on {} because: {}".format(
                                dynastieschat, excp.message))
                except TelegramError:
                    pass

    if undbanned_in_chats == 0:
        send_message(update.effective_message,
                     "This person has been un-dbanned in 0 chats.")
    if undbanned_in_chats > 0:
        send_message(
            update.effective_message,
            "This person has been un-dbanned in {} chats.".format(
                undbanned_in_chats))
    # Also do not spamming all dynasty admins
    """
	DYNASTYADMIN = sql.all_dynasty_users(dynasty_id)
	for x in DYNASTYADMIN:
		getreport = sql.user_dynasties_report(x)
		if getreport is False:
			DYNASTYADMIN.remove(x)
	send_to_list(bot, DYNASTYADMIN,
			 "<b>Un-DynastyBan</b>" \
			 "\n<b>Dynasty:</b> {}" \
			 "\n<b>Dynasty Admin:</b> {}" \
			 "\n<b>User:</b> {}" \
			 "\n<b>User ID:</b> <code>{}</code>".format(info['dname'], mention_html(user.id, user.first_name),
												 mention_html(user_chat.id, user_chat.first_name),
															  user_chat.id),
			html=True)
	"""


@run_async
def set_drules(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not in any Dynasty!")
        return

    if is_user_dynasty_admin(dynasty_id, user.id) is False:
        update.effective_message.reply_text("Only dynasty admins can do this!")
        return

    if len(args) >= 1:
        msg = update.effective_message
        raw_text = msg.text
        args = raw_text.split(
            None, 1)  # use python's maxsplit to separate cmd and args
        if len(args) == 2:
            txt = args[1]
            offset = len(txt) - len(
                raw_text)  # set correct offset relative to command
            markdown_rules = markdown_parser(
                txt, entities=msg.parse_entities(), offset=offset)
        x = sql.set_drules(dynasty_id, markdown_rules)
        if not x:
            update.effective_message.reply_text(
                "Whoa! There was an error while setting Dynasty rules! If you wondered why please ask it in @HackfreaksSupport !"
            )
            return

        rules = sql.get_dynasty_info(dynasty_id)['drules']
        getdynasty = sql.get_dynasty_info(dynasty_id)
        get_dynastylog = sql.get_dynasty_log(dynasty_id)
        if get_dynastylog:
            if eval(get_dynastylog):
                bot.send_message(
                    get_dynastylog,
                    "*{}* has updated Dynasty rules for dynasty *{}*".format(
                        user.first_name, getdynasty['dname']),
                    parse_mode="markdown")
        update.effective_message.reply_text(
            f"Rules have been changed to :\n{rules}!")
    else:
        update.effective_message.reply_text(
            "Please write rules to set this up!")


@run_async
def get_drules(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)
    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not in any Dynasty!")
        return

    rules = sql.get_drules(dynasty_id)
    text = "*Rules in this dynasty:*\n"
    text += rules
    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@run_async
def dynasty_broadcast(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    if args:
        chat = update.effective_chat
        dynasty_id = sql.get_dynasty_id(chat.id)
        dynastyinfo = sql.get_dynasty_info(dynasty_id)
        if is_user_dynasty_owner(dynasty_id, user.id) is False:
            update.effective_message.reply_text(
                "Only Dynasty owners can do this!")
            return
        # Parsing md
        raw_text = msg.text
        args = raw_text.split(
            None, 1)  # use python's maxsplit to separate cmd and args
        txt = args[1]
        offset = len(txt) - len(
            raw_text)  # set correct offset relative to command
        text_parser = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset)
        text = text_parser
        try:
            broadcaster = user.first_name
        except:
            broadcaster = user.first_name + " " + user.last_name
        text += "\n\n- {}".format(mention_markdown(user.id, broadcaster))
        chat_list = sql.all_dynasty_chats(dynasty_id)
        failed = 0
        for chat in chat_list:
            title = "*New broadcast from Dynasty {}*\n".format(dynastyinfo['dname'])
            try:
                bot.sendMessage(chat, title + text, parse_mode="markdown")
            except TelegramError:
                try:
                    dispatcher.bot.getChat(chat)
                except Unauthorized:
                    failed += 1
                    sql.chat_leave_dynasty(chat)
                    LOGGER.info(
                        "Chat {} has left dynasty {} because I was punched".format(
                            chat, dynastyinfo['dname']))
                    continue
                failed += 1
                LOGGER.warning("Couldn't send broadcast to {}".format(
                    str(chat)))

        send_text = "The Dynasty broadcast is complete"
        if failed >= 1:
            send_text += "{} the group failed to receive the message, probably because it left the Dynasty.".format(
                failed)
        update.effective_message.reply_text(send_text)


@run_async
def dynasty_ban_list(update: Update, context: CallbackContext):
    bot, args, chat_data = context.bot, context.args, context.chat_data
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)
    info = sql.get_dynasty_info(dynasty_id)

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not a part of any Dynasty!")
        return

    if is_user_dynasty_owner(dynasty_id, user.id) is False:
        update.effective_message.reply_text(
            "Only Dynasty owners can do this!")
        return

    user = update.effective_user
    chat = update.effective_chat
    getdban = sql.get_all_dban_users(dynasty_id)
    if len(getdban) == 0:
        update.effective_message.reply_text(
            "The Dynasty ban list of {} is empty".format(info['dname']),
            parse_mode=ParseMode.HTML)
        return

    if args:
        if args[0] == 'json':
            jam = time.time()
            new_jam = jam + 1800
            cek = get_chat(chat.id, chat_data)
            if cek.get('status'):
                if jam <= int(cek.get('value')):
                    waktu = time.strftime("%H:%M:%S %d/%m/%Y",
                                          time.localtime(cek.get('value')))
                    update.effective_message.reply_text(
                        "You can backup your data once every 30 minutes!\nYou can back up data again at `{}`"
                        .format(waktu),
                        parse_mode=ParseMode.MARKDOWN)
                    return
                else:
                    if user.id not in DRAGONS:
                        put_chat(chat.id, new_jam, chat_data)
            else:
                if user.id not in DRAGONS:
                    put_chat(chat.id, new_jam, chat_data)
            backups = ""
            for users in getdban:
                getuserinfo = sql.get_all_dban_users_target(dynasty_id, users)
                json_parser = {
                    "user_id": users,
                    "first_name": getuserinfo['first_name'],
                    "last_name": getuserinfo['last_name'],
                    "user_name": getuserinfo['user_name'],
                    "reason": getuserinfo['reason']
                }
                backups += json.dumps(json_parser)
                backups += "\n"
            with BytesIO(str.encode(backups)) as output:
                output.name = "saitama_dbanned_users.json"
                update.effective_message.reply_document(
                    document=output,
                    filename="saitama_dbanned_users.json",
                    caption="Total {} User are blocked by the Dynasty {}."
                    .format(len(getdban), info['dname']))
            return
        elif args[0] == 'csv':
            jam = time.time()
            new_jam = jam + 1800
            cek = get_chat(chat.id, chat_data)
            if cek.get('status'):
                if jam <= int(cek.get('value')):
                    waktu = time.strftime("%H:%M:%S %d/%m/%Y",
                                          time.localtime(cek.get('value')))
                    update.effective_message.reply_text(
                        "You can back up data once every 30 minutes!\nYou can back up data again at `{}`"
                        .format(waktu),
                        parse_mode=ParseMode.MARKDOWN)
                    return
                else:
                    if user.id not in DRAGONS:
                        put_chat(chat.id, new_jam, chat_data)
            else:
                if user.id not in DRAGONS:
                    put_chat(chat.id, new_jam, chat_data)
            backups = "id,firstname,lastname,username,reason\n"
            for users in getdban:
                getuserinfo = sql.get_all_dban_users_target(dynasty_id, users)
                backups += "{user_id},{first_name},{last_name},{user_name},{reason}".format(
                    user_id=users,
                    first_name=getuserinfo['first_name'],
                    last_name=getuserinfo['last_name'],
                    user_name=getuserinfo['user_name'],
                    reason=getuserinfo['reason'])
                backups += "\n"
            with BytesIO(str.encode(backups)) as output:
                output.name = "saitama_dbanned_users.csv"
                update.effective_message.reply_document(
                    document=output,
                    filename="saitama_dbanned_users.csv",
                    caption="Total {} User are blocked by Dynasty {}."
                    .format(len(getdban), info['dname']))
            return

    text = "<b>{} users have been banned from the Dynasty {}:</b>\n".format(
        len(getdban), info['dname'])
    for users in getdban:
        getuserinfo = sql.get_all_dban_users_target(dynasty_id, users)
        if getuserinfo is False:
            text = "There are no users banned from the Dynasty {}".format(
                info['dname'])
            break
        user_name = getuserinfo['first_name']
        if getuserinfo['last_name']:
            user_name += " " + getuserinfo['last_name']
        text += " • {} (<code>{}</code>)\n".format(
            mention_html(users, user_name), users)

    try:
        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    except:
        jam = time.time()
        new_jam = jam + 1800
        cek = get_chat(chat.id, chat_data)
        if cek.get('status'):
            if jam <= int(cek.get('value')):
                waktu = time.strftime("%H:%M:%S %d/%m/%Y",
                                      time.localtime(cek.get('value')))
                update.effective_message.reply_text(
                    "You can back up data once every 30 minutes!\nYou can back up data again at `{}`"
                    .format(waktu),
                    parse_mode=ParseMode.MARKDOWN)
                return
            else:
                if user.id not in DRAGONS:
                    put_chat(chat.id, new_jam, chat_data)
        else:
            if user.id not in DRAGONS:
                put_chat(chat.id, new_jam, chat_data)
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', text)
        with BytesIO(str.encode(cleantext)) as output:
            output.name = "dbanlist.txt"
            update.effective_message.reply_document(
                document=output,
                filename="dbanlist.txt",
                caption="The following is a list of users who are currently dbanned in the Dynasty {}."
                .format(info['dname']))


@run_async
def dynasty_notif(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    dynasty_id = sql.get_dynasty_id(chat.id)

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not a part of any Dynasty!")
        return

    if args:
        if args[0] in ("yes", "on"):
            sql.set_dynasties_setting(user.id, True)
            msg.reply_text(
                "Reporting Dynasty back up! Every user who is dban / undban you will be notified via PM."
            )
        elif args[0] in ("no", "off"):
            sql.set_dynasties_setting(user.id, False)
            msg.reply_text(
                "Reporting Dynasty has stopped! Every user who is dban / undban you will not be notified via PM."
            )
        else:
            msg.reply_text("Please enter `on`/`off`", parse_mode="markdown")
    else:
        getreport = sql.user_dynasties_report(user.id)
        msg.reply_text(
            "Your current Dynasty report preferences: `{}`".format(
                getreport),
            parse_mode="markdown")


@run_async
def dynasty_chats(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)
    info = sql.get_dynasty_info(dynasty_id)

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not a part of any Dynasty!")
        return

    if is_user_dynasty_admin(dynasty_id, user.id) is False:
        update.effective_message.reply_text(
            "Only Dynasty admins can do this!")
        return

    getlist = sql.all_dynasty_chats(dynasty_id)
    if len(getlist) == 0:
        update.effective_message.reply_text(
            "No users are dbanned from the Dynasty {}".format(info['dname']),
            parse_mode=ParseMode.HTML)
        return

    text = "<b>New chat joined the Dynasty {}:</b>\n".format(info['dname'])
    for chats in getlist:
        try:
            chat_name = dispatcher.bot.getChat(chats).title
        except Unauthorized:
            sql.chat_leave_dynasty(chats)
            LOGGER.info("Chat {} has leave dynasty {} because I was kicked".format(
                chats, info['dname']))
            continue
        text += " • {} (<code>{}</code>)\n".format(chat_name, chats)

    try:
        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    except:
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', text)
        with BytesIO(str.encode(cleantext)) as output:
            output.name = "dynastychats.txt"
            update.effective_message.reply_document(
                document=output,
                filename="dynastychats.txt",
                caption="Here is a list of all the chats that joined the Dynasty {}."
                .format(info['dname']))


@run_async
def dynasty_import_bans(update: Update, context: CallbackContext):
    bot, chat_data = context.bot, context.chat_data
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)
    info = sql.get_dynasty_info(dynasty_id)
    getdynasty = sql.get_dynasty_info(dynasty_id)

    if not dynasty_id:
        update.effective_message.reply_text(
            "This group is not a part of any Dynasty!")
        return

    if is_user_dynasty_owner(dynasty_id, user.id) is False:
        update.effective_message.reply_text(
            "Only Dynasty owners can do this!")
        return

    if msg.reply_to_message and msg.reply_to_message.document:
        jam = time.time()
        new_jam = jam + 1800
        cek = get_chat(chat.id, chat_data)
        if cek.get('status'):
            if jam <= int(cek.get('value')):
                waktu = time.strftime("%H:%M:%S %d/%m/%Y",
                                      time.localtime(cek.get('value')))
                update.effective_message.reply_text(
                    "You can get your data once every 30 minutes!\nYou can get data again at `{}`"
                    .format(waktu),
                    parse_mode=ParseMode.MARKDOWN)
                return
            else:
                if user.id not in DRAGONS:
                    put_chat(chat.id, new_jam, chat_data)
        else:
            if user.id not in DRAGONS:
                put_chat(chat.id, new_jam, chat_data)
        #if int(int(msg.reply_to_message.document.file_size)/1024) >= 200:
        #	msg.reply_text("This file is too big!")
        #	return
        success = 0
        failed = 0
        try:
            file_info = bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text(
                "Try downloading and re-uploading the file, this one seems broken!"
            )
            return
        fileformat = msg.reply_to_message.document.file_name.split('.')[-1]
        if fileformat == 'json':
            multi_dynasty_id = []
            multi_import_userid = []
            multi_import_firstname = []
            multi_import_lastname = []
            multi_import_username = []
            multi_import_reason = []
            with BytesIO() as file:
                file_info.download(out=file)
                file.seek(0)
                reading = file.read().decode('UTF-8')
                splitting = reading.split('\n')
                for x in splitting:
                    if x == '':
                        continue
                    try:
                        data = json.loads(x)
                    except json.decoder.JSONDecodeError as err:
                        failed += 1
                        continue
                    try:
                        import_userid = int(data['user_id'])  # Make sure it int
                        import_firstname = str(data['first_name'])
                        import_lastname = str(data['last_name'])
                        import_username = str(data['user_name'])
                        import_reason = str(data['reason'])
                    except ValueError:
                        failed += 1
                        continue
                    # Checking user
                    if int(import_userid) == bot.id:
                        failed += 1
                        continue
                    if is_user_dynasty_owner(dynasty_id, import_userid) is True:
                        failed += 1
                        continue
                    if is_user_dynasty_admin(dynasty_id, import_userid) is True:
                        failed += 1
                        continue
                    if str(import_userid) == str(OWNER_ID):
                        failed += 1
                        continue
                    if int(import_userid) in DRAGONS:
                        failed += 1
                        continue
                    if int(import_userid) in TIGERS:
                        failed += 1
                        continue
                    if int(import_userid) in WOLVES:
                        failed += 1
                        continue
                    multi_dynasty_id.append(dynasty_id)
                    multi_import_userid.append(str(import_userid))
                    multi_import_firstname.append(import_firstname)
                    multi_import_lastname.append(import_lastname)
                    multi_import_username.append(import_username)
                    multi_import_reason.append(import_reason)
                    success += 1
                sql.multi_dban_user(multi_dynasty_id, multi_import_userid,
                                    multi_import_firstname,
                                    multi_import_lastname,
                                    multi_import_username, multi_import_reason)
            text = "Blocks were successfully imported. {} people are blocked.".format(
                success)
            if failed >= 1:
                text += " {} Failed to import.".format(failed)
            get_dynastylog = sql.get_dynasty_log(dynasty_id)
            if get_dynastylog:
                if eval(get_dynastylog):
                    teks = "Dynasty *{}* has successfully imported data. {} banned.".format(
                        getdynasty['dname'], success)
                    if failed >= 1:
                        teks += " {} Failed to import.".format(failed)
                    bot.send_message(get_dynastylog, teks, parse_mode="markdown")
        elif fileformat == 'csv':
            multi_dynasty_id = []
            multi_import_userid = []
            multi_import_firstname = []
            multi_import_lastname = []
            multi_import_username = []
            multi_import_reason = []
            file_info.download("dban_{}.csv".format(
                msg.reply_to_message.document.file_id))
            with open(
                    "dban_{}.csv".format(msg.reply_to_message.document.file_id),
                    'r',
                    encoding="utf8") as csvFile:
                reader = csv.reader(csvFile)
                for data in reader:
                    try:
                        import_userid = int(data[0])  # Make sure it int
                        import_firstname = str(data[1])
                        import_lastname = str(data[2])
                        import_username = str(data[3])
                        import_reason = str(data[4])
                    except ValueError:
                        failed += 1
                        continue
                    # Checking user
                    if int(import_userid) == bot.id:
                        failed += 1
                        continue
                    if is_user_dynasty_owner(dynasty_id, import_userid) is True:
                        failed += 1
                        continue
                    if is_user_dynasty_admin(dynasty_id, import_userid) is True:
                        failed += 1
                        continue
                    if str(import_userid) == str(OWNER_ID):
                        failed += 1
                        continue
                    if int(import_userid) in DRAGONS:
                        failed += 1
                        continue
                    if int(import_userid) in TIGERS:
                        failed += 1
                        continue
                    if int(import_userid) in WOLVES:
                        failed += 1
                        continue
                    multi_dynasty_id.append(dynasty_id)
                    multi_import_userid.append(str(import_userid))
                    multi_import_firstname.append(import_firstname)
                    multi_import_lastname.append(import_lastname)
                    multi_import_username.append(import_username)
                    multi_import_reason.append(import_reason)
                    success += 1
                    # t = ThreadWithReturnValue(target=sql.dban_user, args=(dynasty_id, str(import_userid), import_firstname, import_lastname, import_username, import_reason,))
                    # t.start()
                sql.multi_dban_user(multi_dynasty_id, multi_import_userid,
                                    multi_import_firstname,
                                    multi_import_lastname,
                                    multi_import_username, multi_import_reason)
            csvFile.close()
            os.remove("dban_{}.csv".format(
                msg.reply_to_message.document.file_id))
            text = "Files were imported successfully. {} people banned.".format(
                success)
            if failed >= 1:
                text += " {} Failed to import.".format(failed)
            get_dynastylog = sql.get_dynasty_log(dynasty_id)
            if get_dynastylog:
                if eval(get_dynastylog):
                    teks = "Dynasty *{}* has successfully imported data. {} banned.".format(
                        getdynasty['dname'], success)
                    if failed >= 1:
                        teks += " {} Failed to import.".format(failed)
                    bot.send_message(get_dynastylog, teks, parse_mode="markdown")
        else:
            send_message(update.effective_message,
                         "This file is not supported.")
            return
        send_message(update.effective_message, text)


@run_async
def del_dynasty_button(update: Update, context: CallbackContext):
    query = update.callback_query
    userid = query.message.chat.id
    dynasty_id = query.data.split("_")[1]

    if dynasty_id == 'cancel':
        query.message.edit_text("Dynasty deletion cancelled")
        return

    getdynasty = sql.get_dynasty_info(dynasty_id)
    if getdynasty:
        delete = sql.del_dynasty(dynasty_id)
        if delete:
            query.message.edit_text(
                "You have removed your Dynasty! Now all the Groups that are connected with `{}` do not have a Dynasty."
                .format(getdynasty['dname']),
                parse_mode='markdown')


@run_async
def dynasty_stat_user(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if args:
        if args[0].isdigit():
            user_id = args[0]
        else:
            user_id = extract_user(msg, args)
    else:
        user_id = extract_user(msg, args)

    if user_id:
        if len(args) == 2 and args[0].isdigit():
            dynasty_id = args[1]
            user_name, reason, dbantime = sql.get_user_dban(
                dynasty_id, str(user_id))
            if dbantime:
                dbantime = time.strftime("%d/%m/%Y", time.localtime(dbantime))
            else:
                dbantime = "Unavaiable"
            if user_name is False:
                send_message(
                    update.effective_message,
                    "Dynasty {} not found!".format(dynasty_id),
                    parse_mode="markdown")
                return
            if user_name == "" or user_name is None:
                user_name = "He/she"
            if not reason:
                send_message(
                    update.effective_message,
                    "{} is not banned in this Dynasty!".format(user_name))
            else:
                teks = "{} banned in this Dynasty because:\n`{}`\n*Banned at:* `{}`".format(
                    user_name, reason, dbantime)
                send_message(
                    update.effective_message, teks, parse_mode="markdown")
            return
        user_name, dbanlist = sql.get_user_dbanlist(str(user_id))
        if user_name == "":
            try:
                user_name = bot.get_chat(user_id).first_name
            except BadRequest:
                user_name = "He/she"
            if user_name == "" or user_name is None:
                user_name = "He/she"
        if len(dbanlist) == 0:
            send_message(
                update.effective_message,
                "{} is not banned in any Dynasty!".format(user_name))
            return
        else:
            teks = "{} has been banned in this Dynasty:\n".format(user_name)
            for x in dbanlist:
                teks += "- `{}`: {}\n".format(x[0], x[1][:20])
            teks += "\nIf you want to find out more about the reasons for Dynastyban specifically, use /dbanstat <DynastyID>"
            send_message(update.effective_message, teks, parse_mode="markdown")

    elif not msg.reply_to_message and not args:
        user_id = msg.from_user.id
        user_name, dbanlist = sql.get_user_dbanlist(user_id)
        if user_name == "":
            user_name = msg.from_user.first_name
        if len(dbanlist) == 0:
            send_message(
                update.effective_message,
                "{} is not banned in any Dynasty!".format(user_name))
        else:
            teks = "{} has been banned in this Dynasty:\n".format(user_name)
            for x in dbanlist:
                teks += "- `{}`: {}\n".format(x[0], x[1][:20])
            teks += "\nIf you want to find out more about the reasons for Dynastyban specifically, use /dbanstat <DynastyID>"
            send_message(update.effective_message, teks, parse_mode="markdown")

    else:
        dynasty_id = args[0]
        dynastyinfo = sql.get_dynasty_info(dynasty_id)
        if not dynastyinfo:
            send_message(update.effective_message,
                         "Dynasty {} not found!".format(dynasty_id))
            return
        name, reason, dbantime = sql.get_user_dban(dynasty_id, msg.from_user.id)
        if dbantime:
            dbantime = time.strftime("%d/%m/%Y", time.localtime(dbantime))
        else:
            dbantime = "Unavaiable"
        if not name:
            name = msg.from_user.first_name
        if not reason:
            send_message(update.effective_message,
                         "{} is not banned in this Dynasty".format(name))
            return
        send_message(
            update.effective_message,
            "{} banned in this Dynasty because:\n`{}`\n*Banned at:* `{}`"
            .format(name, reason, dbantime),
            parse_mode="markdown")


@run_async
def set_dynasty_log(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    if args:
        dynastyinfo = sql.get_dynasty_info(args[0])
        if not dynastyinfo:
            send_message(update.effective_message,
                         "This Dynasty does not exist!")
            return
        isowner = is_user_dynasty_owner(args[0], user.id)
        if not isowner:
            send_message(update.effective_message,
                         "Only Dynasty creator can set Dynasty logs.")
            return
        setlog = sql.set_dynasty_log(args[0], chat.id)
        if setlog:
            send_message(
                update.effective_message,
                "Dynasty log `{}` has been set to {}".format(
                    dynastyinfo['dname'], chat.title),
                parse_mode="markdown")
    else:
        send_message(update.effective_message,
                     "You have not provided your dynastyrated ID!")


@run_async
def unset_dynasty_log(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    if args:
        dynastyinfo = sql.get_dynasty_info(args[0])
        if not dynastyinfo:
            send_message(update.effective_message,
                         "This Dynasty does not exist!")
            return
        isowner = is_user_dynasty_owner(args[0], user.id)
        if not isowner:
            send_message(update.effective_message,
                         "Only Dynasty creator can set Dynasty logs.")
            return
        setlog = sql.set_dynasty_log(args[0], None)
        if setlog:
            send_message(
                update.effective_message,
                "Dynasty log `{}` has been revoked on {}".format(
                    dynastyinfo['dname'], chat.title),
                parse_mode="markdown")
    else:
        send_message(update.effective_message,
                     "You have not provided your dynastyrated ID!")


@run_async
def subs_dynasties(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)
    dynastyinfo = sql.get_dynasty_info(dynasty_id)

    if not dynasty_id:
        send_message(update.effective_message,
                     "This group is not in any Dynasty!")
        return

    if is_user_dynasty_owner(dynasty_id, user.id) is False:
        send_message(update.effective_message, "Only dynasty owner can do this!")
        return

    if args:
        getdynasty = sql.search_dynasty_by_id(args[0])
        if getdynasty is False:
            send_message(update.effective_message,
                         "Please enter a valid Dynasty id.")
            return
        subdynasty = sql.subs_dynasty(args[0], dynasty_id)
        if subdynasty:
            send_message(
                update.effective_message,
                "Dynasty `{}` has subscribe the Dynasty `{}`. Every time there is a Dynastyban from that Dynasty, this Dynasty will also banned that user."
                .format(dynastyinfo['dname'], getdynasty['dname']),
                parse_mode="markdown")
            get_dynastylog = sql.get_dynasty_log(args[0])
            if get_dynastylog:
                if int(get_dynastylog) != int(chat.id):
                    bot.send_message(
                        get_dynastylog,
                        "Dynasty `{}` has subscribe the Dynasty `{}`"
                        .format(dynastyinfo['dname'], getdynasty['dname']),
                        parse_mode="markdown")
        else:
            send_message(
                update.effective_message,
                "Dynasty `{}` already subscribe the Dynasty `{}`.".format(
                    dynastyinfo['dname'], getdynasty['dname']),
                parse_mode="markdown")
    else:
        send_message(update.effective_message,
                     "You have not provided your dynastyrated ID!")


@run_async
def unsubs_dynasties(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)
    dynastyinfo = sql.get_dynasty_info(dynasty_id)

    if not dynasty_id:
        send_message(update.effective_message,
                     "This group is not in any Dynasty!")
        return

    if is_user_dynasty_owner(dynasty_id, user.id) is False:
        send_message(update.effective_message, "Only dynasty owner can do this!")
        return

    if args:
        getdynasty = sql.search_dynasty_by_id(args[0])
        if getdynasty is False:
            send_message(update.effective_message,
                         "Please enter a valid Dynasty id.")
            return
        subdynasty = sql.unsubs_dynasty(args[0], dynasty_id)
        if subdynasty:
            send_message(
                update.effective_message,
                "Dynasty `{}` now unsubscribe dynasty `{}`.".format(
                    dynastyinfo['dname'], getdynasty['dname']),
                parse_mode="markdown")
            get_dynastylog = sql.get_dynasty_log(args[0])
            if get_dynastylog:
                if int(get_dynastylog) != int(chat.id):
                    bot.send_message(
                        get_dynastylog,
                        "Dynasty `{}` has unsubscribe dynasty `{}`.".format(
                            dynastyinfo['dname'], getdynasty['dname']),
                        parse_mode="markdown")
        else:
            send_message(
                update.effective_message,
                "Dynasty `{}` is not subscribing `{}`.".format(
                    dynastyinfo['dname'], getdynasty['dname']),
                parse_mode="markdown")
    else:
        send_message(update.effective_message,
                     "You have not provided your dynastyrated ID!")


@run_async
def get_mydynastiesubs(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == 'private':
        send_message(update.effective_message,
                     "This command is specific to the group, not to our pm!")
        return

    dynasty_id = sql.get_dynasty_id(chat.id)
    dynastyinfo = sql.get_dynasty_info(dynasty_id)

    if not dynasty_id:
        send_message(update.effective_message,
                     "This group is not in any Dynasty!")
        return

    if is_user_dynasty_owner(dynasty_id, user.id) is False:
        send_message(update.effective_message, "Only dynasty owner can do this!")
        return

    try:
        getmy = sql.get_mysubs(dynasty_id)
    except:
        getmy = []

    if len(getmy) == 0:
        send_message(
            update.effective_message,
            "Dynasty `{}` is not subscribing any Dynasty.".format(
                dynastyinfo['dname']),
            parse_mode="markdown")
        return
    else:
        listdynasty = "Dynasty `{}` is subscribing Dynasty:\n".format(
            dynastyinfo['dname'])
        for x in getmy:
            listdynasty += "- `{}`\n".format(x)
        listdynasty += "\nTo get dynasty info `/dynastyinfo <dynastyid>`. To unsubscribe `/unsubdynasty <dynastyid>`."
        send_message(update.effective_message, listdynasty, parse_mode="markdown")


@run_async
def get_mydynasties_list(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    dynastyowner = sql.get_user_owner_dynasty_full(user.id)
    if dynastyowner:
        text = "*You are owner of dynasties:\n*"
        for f in dynastyowner:
            text += "- `{}`: *{}*\n".format(f['dynasty_id'], f['dynasty']['dname'])
    else:
        text = "*You are not have any dynasties!*"
    send_message(update.effective_message, text, parse_mode="markdown")


def is_user_dynasty_admin(dynasty_id, user_id):
    dynasty_admins = sql.all_dynasty_users(dynasty_id)
    if dynasty_admins is False:
        return False
    if int(user_id) in dynasty_admins or int(user_id) == OWNER_ID:
        return True
    else:
        return False


def is_user_dynasty_owner(dynasty_id, user_id):
    getsql = sql.get_dynasty_info(dynasty_id)
    if getsql is False:
        return False
    getdynastyowner = eval(getsql['dusers'])
    if getdynastyowner is None or getdynastyowner is False:
        return False
    getdynastyowner = getdynastyowner['owner']
    if str(user_id) == getdynastyowner or int(user_id) == OWNER_ID:
        return True
    else:
        return False


# There's no handler for this yet, but updating for v12 in case its used
@run_async
def welcome_dynasty(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    dynasty_id = sql.get_dynasty_id(chat.id)
    dban, dbanreason, dbantime = sql.get_dban_user(dynasty_id, user.id)
    if dban:
        update.effective_message.reply_text(
            "This user is banned in current Dynasty! I will remove him.")
        bot.kick_chat_member(chat.id, user.id)
        return True
    else:
        return False


def __stats__():
    all_dbanned = sql.get_all_dban_users_global()
    all_dynasties = sql.get_all_dynasties_users_global()
    return "• {} banned users across {} Dynasty".format(
        len(all_dbanned), len(all_dynasties))


def __user_info__(user_id, chat_id):
    dynasty_id = sql.get_dynasty_id(chat_id)
    if dynasty_id:
        dban, dbanreason, dbantime = sql.get_dban_user(dynasty_id, user_id)
        info = sql.get_dynasty_info(dynasty_id)
        infoname = info['dname']

        if int(info['owner']) == user_id:
            text = "Dynasty owner of: <b>{}</b>.".format(infoname)
        elif is_user_dynasty_admin(dynasty_id, user_id):
            text = "Dynasty admin of: <b>{}</b>.".format(infoname)

        elif dban:
            text = "Dynasty banned: <b>Yes</b>"
            text += "\n<b>Reason:</b> {}".format(dbanreason)
        else:
            text = "Dynasty banned: <b>No</b>"
    else:
        text = ""
    return text


# Temporary data
def put_chat(chat_id, value, chat_data):
    # print(chat_data)
    if value is False:
        status = False
    else:
        status = True
    chat_data[chat_id] = {'Dynasty': {"status": status, "value": value}}


def get_chat(chat_id, chat_data):
    # print(chat_data)
    try:
        value = chat_data[chat_id]['Dynasty']
        return value
    except KeyError:
        return {"status": False, "value": False}


@run_async
def dynasty_owner_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        """*👑 Dynasty Owner Only:*
 • `/newdynasty <dynasty_name>`*:* Creates a Dynasty, One allowed per user
 • `/renamedynasty <dynasty_id> <new_dynasty_name>`*:* Renames the dynasty id to a new name
 • `/deldynasty <dynasty_id>`*:* Delete a Dynasty, and any information related to it. Will not cancel blocked users
 • `/dpromote <user>`*:* Assigns the user as a Dynasty admin. Enables all commands for the user under `Dynasty Admins`
 • `/ddemote <user>`*:* Drops the User from the admin Dynasty to a normal User
 • `/subdynasty <dynasty_id>`*:* Subscribes to a given dynasty ID, bans from that subscribed dynasty will also happen in your dynasty
 • `/unsubdynasty <dynasty_id>`*:* Unsubscribes to a given dynasty ID
 • `/setdynastylog <dynasty_id>`*:* Sets the group as a dynasty log report base for the Dynasty
 • `/unsetdynastylog <dynasty_id>`*:* Removed the group as a dynasty log report base for the Dynasty
 • `/fbroadcast <message>`*:* Broadcasts a messages to all groups that have joined your dynasty
 • `/dynastiesubs`*:* Shows the dynasties your group is subscribed to `(broken rn)`""",
        parse_mode=ParseMode.MARKDOWN)


@run_async
def dynasty_admin_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        """*🔱 Dynasty Admins:*
 • `/dban <user> <reason>`*:* Dynasty bans a user
 • `/undban <user> <reason>`*:* Removes a user from a dynasty ban
 • `/dynastyinfo <dynasty_id>`*:* Information about the specified Dynasty
 • `/joindynasty <dynasty_id>`*:* Join the current chat to the Dynasty. Only chat owners can do this. Every chat can only be in one Dynasty
 • `/leavedynasty <dynasty_id>`*:* Leave the Dynasty given. Only chat owners can do this
 • `/setdrules <rules>`*:* Arrange Dynasty rules
 • `/dynastyadmins`*:* Show Dynasty admin
 • `/dbanlist`*:* Displays all users who are victimized at the Dynasty at this time
 • `/dynastychats`*:* Get all the chats that are connected in the Dynasty
 • `/chatdynasty `*:* See the Dynasty in the current chat\n""",
        parse_mode=ParseMode.MARKDOWN)


@run_async
def dynasty_user_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        """*🎩 Any user:*
 • `/dbanstat`*:* Shows if you/or the user you are replying to or their username is dbanned somewhere or not
 • `/dynastynotif <on/off>`*:* Dynasty settings not in PM when there are users who are dbaned/undbanned
 • `/drules`*:* See Dynasty regulations\n""",
        parse_mode=ParseMode.MARKDOWN)


__mod_name__ = "Dynasty"

__help__ = """
Everything is fun, until a spammer starts entering your group, and you have to block it. Then you need to start banning more, and more, and it hurts.
But then you have many groups, and you don't want this spammer to be in one of your groups - how can you deal? Do you have to manually block it, in all your groups?\n
*No longer!* With Dynasty, you can make a ban in one chat overlap with all other chats.\n
You can even designate Dynasty admins, so your trusted admin can ban all the spammers from chats you want to protect.\n

*Commands:*\n
Dynastys are now divided into 3 sections for your ease. 
• `/dynastyownerhelp`*:* Provides help for dynasty creation and owner only commands
• `/dynastyadminhelp`*:* Provides help for dynasty administration commands
• `/dynastyuserhelp`*:* Provides help for commands anyone can use

"""

NEW_DYNASTY_HANDLER = CommandHandler("newdynasty", new_dynasty)
DEL_DYNASTY_HANDLER = CommandHandler("deldynasty", del_dynasty)
RENAME_DYNASTY = CommandHandler("renamedynasty", rename_dynasty)
JOIN_DYNASTY_HANDLER = CommandHandler("joindynasty", join_dynasty)
LEAVE_DYNASTY_HANDLER = CommandHandler("leavedynasty", leave_dynasty)
PROMOTE_DYNASTY_HANDLER = CommandHandler("dpromote", user_join_dynasty)
DEMOTE_DYNASTY_HANDLER = CommandHandler("ddemote", user_demote_dynasty)
INFO_DYNASTY_HANDLER = CommandHandler("dynastyinfo", dynasty_info)
BAN_DYNASTY_HANDLER = DisableAbleCommandHandler("dban", dynasty_ban)
UN_BAN_DYNASTY_HANDLER = CommandHandler("undban", undban)
DYNASTY_BROADCAST_HANDLER = CommandHandler("fbroadcast", dynasty_broadcast)
DYNASTY_SET_RULES_HANDLER = CommandHandler("setdrules", set_drules)
DYNASTY_GET_RULES_HANDLER = CommandHandler("drules", get_drules)
DYNASTY_CHAT_HANDLER = CommandHandler("chatdynasty", dynasty_chat)
DYNASTY_ADMIN_HANDLER = CommandHandler("dynastyadmins", dynasty_admin)
DYNASTY_USERBAN_HANDLER = CommandHandler("dbanlist", dynasty_ban_list)
DYNASTY_NOTIF_HANDLER = CommandHandler("dynastynotif", dynasty_notif)
DYNASTY_CHATLIST_HANDLER = CommandHandler("dynastychats", dynasty_chats)
DYNASTY_IMPORTBAN_HANDLER = CommandHandler("importdbans", dynasty_import_bans)
DYNASTYSTAT_USER = DisableAbleCommandHandler(["dynastystat", "dbanstat"], dynasty_stat_user)
SET_DYNASTY_LOG = CommandHandler("setdynastylog", set_dynasty_log)
UNSET_DYNASTY_LOG = CommandHandler("unsetdynastylog", unset_dynasty_log)
SUBS_DYNASTY = CommandHandler("subdynasty", subs_dynasties)
UNSUBS_DYNASTY = CommandHandler("unsubdynasty", unsubs_dynasties)
MY_SUB_DYNASTY = CommandHandler("dynastiesubs", get_mydynastiesubs)
MY_DYNASTYS_LIST = CommandHandler("mydynasties", get_mydynasties_list)
DELETEBTN_DYNASTY_HANDLER = CallbackQueryHandler(del_dynasty_button, pattern=r"rmdynasty_")
DYNASTY_OWNER_HELP_HANDLER = CommandHandler("dynastyownerhelp", dynasty_owner_help)
DYNASTY_ADMIN_HELP_HANDLER = CommandHandler("dynastyadminhelp", dynasty_admin_help)
DYNASTY_USER_HELP_HANDLER = CommandHandler("dynastyuserhelp", dynasty_user_help)

dispatcher.add_handler(NEW_DYNASTY_HANDLER)
dispatcher.add_handler(DEL_DYNASTY_HANDLER)
dispatcher.add_handler(RENAME_DYNASTY)
dispatcher.add_handler(JOIN_DYNASTY_HANDLER)
dispatcher.add_handler(LEAVE_DYNASTY_HANDLER)
dispatcher.add_handler(PROMOTE_DYNASTY_HANDLER)
dispatcher.add_handler(DEMOTE_DYNASTY_HANDLER)
dispatcher.add_handler(INFO_DYNASTY_HANDLER)
dispatcher.add_handler(BAN_DYNASTY_HANDLER)
dispatcher.add_handler(UN_BAN_DYNASTY_HANDLER)
dispatcher.add_handler(DYNASTY_BROADCAST_HANDLER)
dispatcher.add_handler(DYNASTY_SET_RULES_HANDLER)
dispatcher.add_handler(DYNASTY_GET_RULES_HANDLER)
dispatcher.add_handler(DYNASTY_CHAT_HANDLER)
dispatcher.add_handler(DYNASTY_ADMIN_HANDLER)
dispatcher.add_handler(DYNASTY_USERBAN_HANDLER)
dispatcher.add_handler(DYNASTY_NOTIF_HANDLER)
dispatcher.add_handler(DYNASTY_CHATLIST_HANDLER)
dispatcher.add_handler(DYNASTY_IMPORTBAN_HANDLER)
dispatcher.add_handler(DYNASTYSTAT_USER)
dispatcher.add_handler(SET_DYNASTY_LOG)
dispatcher.add_handler(UNSET_DYNASTY_LOG)
dispatcher.add_handler(SUBS_DYNASTY)
dispatcher.add_handler(UNSUBS_DYNASTY)
dispatcher.add_handler(MY_SUB_DYNASTY)
dispatcher.add_handler(MY_DYNASTYS_LIST)
dispatcher.add_handler(DELETEBTN_DYNASTY_HANDLER)
dispatcher.add_handler(DYNASTY_OWNER_HELP_HANDLER)
dispatcher.add_handler(DYNASTY_ADMIN_HELP_HANDLER)
dispatcher.add_handler(DYNASTY_USER_HELP_HANDLER)
