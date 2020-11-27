from Sibyl_System import System, SIBYL, ENFORCERS, Sibyl_logs, system_cmd
import re
import Sibyl_System.plugins.Mongo_DB.message_blacklist as db
import Sibyl_System.plugins.Mongo_DB.name_blacklist as wlc_collection
from telethon import events

async def extract(flag, event):
    if flag:
        return re.escape(flag.group(1))
    else:
        try:
            text = event.text.split(" ", 1)[1]
            return text
        except BaseException:
            return False


@System.on(system_cmd(pattern=r'addbl ', allow_slash=False))
async def addbl(event) -> None:
    flag = re.match(".addbl -e (.*)", event.text, re.DOTALL)
    text = await extract(flag, event)
    if not text: return
    a = await db.update_blacklist(text, add=True)
    if a:
        await System.send_message(event.chat_id, f"Added {text} to blacklist")
    else:
        await System.send_message(event.chat_id, f" {text} is already blacklisted")


@System.on(system_cmd(pattern=r'addwlcbl '))
async def wlcbl(event) -> None:
    flag = re.match(".addwlcbl -e (.*)", event.text, re.DOTALL)
    text = await extract(flag, event)
    if not text: return
    a = await wlc_collection.update_wlc_blacklist(text, add=True)
    if a:
        await System.send_message(event.chat_id, f"Added {text} to blacklist")
    else:
        await System.send_message(event.chat_id, f" {text} is already blacklisted")


@System.on(system_cmd(pattern=r'rmwlcbl '))
async def rmwlcbl(event):
    try:
        text = event.text.split(" ", 1)[1]
    except BaseException:
        return
    a = await wlc_collection.update_wlc_blacklist(text, add=False)
    if a:
        await System.send_message(event.chat_id, f"Removed {text} from blacklist")
    else:
        await System.send_message(event.chat_id, f"{text} is not blacklisted")


@System.on(system_cmd(pattern=r'rmbl ', allow_slash=False))
async def rmbl(event):
    try:
        text = event.text.split(" ", 1)[1]
    except BaseException:
        return
    a = await db.update_blacklist(text, add=False)
    if a:
        await System.send_message(event.chat_id, f"Removed {text} from blacklist")
    else:
        await System.send_message(event.chat_id, f"{text} is not blacklisted")


@System.on(system_cmd(pattern=r'listbl'))
async def listbl(event):
    bl_list = await db.get_blacklist()
    msg = "Currently Blacklisted strings:\n"
    for x in bl_list:
        msg += f"•`{x}`\n"
    await System.send_message(event.chat_id, msg)


@System.on(events.MessageEdited(incoming=True))
@System.on(events.NewMessage(incoming=True))
async def auto_gban_request(event):
    System.processing += 1
    if event.from_id in ENFORCERS or event.from_id in SIBYL:
        return
    if event.chat_id == Sibyl_logs:
        return
    text = event.text
    words = await db.get_blacklist()
    if words:
        for word in words:
            pattern = r"( |^|[^\w])" + word + r"( |$|[^\w])"
            if re.search(pattern, text, flags=re.IGNORECASE):
                c = words.index(word)
                link = f"t.me/{event.chat.username}/{event.message.id}" if event.chat.username else f"Occurred in Private Chat - {event.chat.title}"
                logmsg = f"""$AUTOSCAN\n**Scanned user:** [{event.from_id}](tg://user?id={event.from_id})\n**Reason:** 0x{c}\n**Chat:** {link}\n**Hue Color:** Yellow-green\n**Message:** {event.text}"""
                await System.send_message(Sibyl_logs, logmsg)
                System.processed += 1
                System.processing -= 1
                return
    System.processed += 1
    System.processing -= 1


@System.on(events.ChatAction(func= lambda e: e.user_joined))  # pylint:disable=E0602
async def auto_wlc_gban(event):
    System.processing += 1
    user = await event.get_user()
    if user.id in ENFORCERS or user.id in SIBYL:
        return
    words = await wlc_collection.get_wlc_bl()
    if words:
       text = user.first_name
       if user.last_name: text = text + " " + user.last_name
       for word in words:
          pattern = r"( |^|[^\w])" + word + r"( |$|[^\w])"
          if re.search(pattern, text, flags=re.IGNORECASE):
             c = words.index(word)
             logmsg = f"""$AUTOSCAN\n**Scanned user:** [{user.id}](tg://user?id={user.id})\n**Reason:** 1x{c}\n**User joined and blacklisted string in name**\n**Matched String:** {word}\n"""
             await System.send_message(Sibyl_logs, logmsg)
             System.processed += 1
             System.processing -= 1
             return
       System.processed += 1
       System.processing -= 1

@System.on(system_cmd(pattern=r'get ', allow_slash=False))
async def get(event):
    try:
        text = event.text.split(" ", 1)[1]
    except BaseException:
        return
    if text.startswith('0'):
         words = await db.get_blacklist()
    elif text.startswith('1'):
         words = await wlc_collection.get_wlc_bl()
    else:
         return
    which = re.match('.get (\d)x(\d+)', event.text)
    if which:
       try:
          await event.reply(f"Info from type {which.group(1)}\nPostion: {which.group(2)}\nMatches:{words[int(which.group(2))]}")
       except Exception:
          return


__plugin_name__ = "blacklist"

help_plus = """
Here is help for **String Blacklist**
`/addbl` - **Add trigger to blacklist**
`/rmbl` - **remove trigger from blacklist**
`/listbl` - **list blacklisted words**
Here is help for **Welcome Name-String Blacklist**
`/addwlcbl` - **Add new blacklisted name-string**
`/rmwlcbl` - **Remove blacklisted welcome-name-string**
Flags( -e // escape text ) to addbl & addwlcbl
`/get` - **Get Match from yxy **
**Notes:**
`/` `?` `.` `!` are supported prefixes.
**Example:** `/addbl` or `?addbl` or `.addbl`
"""
