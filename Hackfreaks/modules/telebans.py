from Hackfreaks import telethn
from telethon import events
from Hackfreaks.modules.helper_funcs.telethn.chatstatus import (
    can_ban_users, user_is_admin)
from telegram import User
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights


@telethn.on(events.NewMessage(pattern="^[!/]dkick$"))
async def dkick(event):

    if not await user_is_admin(
            user_id=event.from_id, message=event) and event.from_id not in [
                1167145475, 1087968824
            ]:
        await event.reply("Only Admins can execute this command!")
        return

    if not await can_ban_users(message=event):
        await event.reply("I don't have enough rights to do that!")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply("Reply to someone to delete it and kick the user!")
        return


    x = (await event.get_reply_message()).sender_id
    zx = (await event.get_reply_message())
    await zx.delete()
    await telethn.kick_participant(event.chat_id, x)

@telethn.on(events.NewMessage(pattern="^[!/]dban$"))
async def dban(event):

    if not await user_is_admin(
            user_id=event.from_id, message=event) and event.from_id not in [
                1167145475, 1087968824
            ]:
        await event.reply("Only Admins can execute this command!")
        return

    if not await can_ban_users(message=event):
        await event.reply("I don't have enough rights to do that!")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply("Reply to someone to delete the message and ban the user!")
        return

    x = (await event.get_reply_message()).sender_id
    zx = (await event.get_reply_message())
    await zx.delete()
    await telethn(EditBannedRequest(event.chat_id, x, ChatBannedRights(until_date=None, view_messages=True)))

@telethn.on(events.NewMessage(pattern="^[!/]sban$"))
async def dban(event):

    if not await user_is_admin(
            user_id=event.from_id, message=event) and event.from_id not in [
                1167145475, 1087968824
            ]:
        await event.reply("Only Admins can execute this command!")
        return

    if not await can_ban_users(message=event):
        await event.reply("I don't have enough rights to do that!")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply("Reply to someone to delete the message and ban the user!")
        return

    x = (await event.get_reply_message()).sender_id
    zx = (await event.get_reply_message())
    await event.delete()
    await telethn(EditBannedRequest(event.chat_id, x, ChatBannedRights(until_date=None, view_messages=True)))
