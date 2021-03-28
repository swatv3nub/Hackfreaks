from tswift import Song

from telegram import Update, Message, Chat
from telegram.ext import CallbackContext, run_async

from Hackfreaks import dispatcher
from Hackfreaks.modules.disable import DisableAbleCommandHandler


@run_async
def lyrics(update, context):
    msg = update.effective_message
    args = msg.text.strip().split(" ", 1)
    try:
        query = str(args[1])
    except:
        if msg.reply_to_message:
            query = msg.reply_to_message.text
        else:
            update.effective_message.reply_text("You haven't specified which song to look for!")
            return
    song = Song.find_song(query)
    if song:
        if song.lyrics:
            reply = song.format()
        else:
            reply = "Couldn't find any lyrics for that song!"
    else:
        reply = "Song not found!"
    if len(reply) > 4090:
        with open("lyrics.txt", 'w') as f:
            f.write(f"{reply}\n\n\nOwO UwU OmO")
        with open("lyrics.txt", 'rb') as f:
            msg.reply_document(document=f,
            caption="Message length exceeded max limit! Sending as a text file.")
    else:
        msg.reply_text(reply)
                
        
                
__help__ = """
Want to get the lyrics of your favorite songs straight from the app? Plus You can get the Song uploaded here on your request
*Available commands:*
 - /lyrics <song>: returns the lyrics of that song.
 - /song <song>: uploads the song directly to telegram from youtube.
 You can either enter just the song name or both the artist and song name.
"""

__mod_name__ = "Music"



LYRICS_HANDLER = DisableAbleCommandHandler("lyrics", lyrics)

dispatcher.add_handler(LYRICS_HANDLER)
