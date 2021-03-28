from Hackfreaks.pyroutils import capture_err

from pyrogram import filters
from pyrogram.types import Message

from Hackfreaks import pyromode



@pyromode.on_message(filters.command(["encrypt", "enc"] & ~filters.edited)
@capture_err
async def encrypt(_, message: Message):
    if not message.reply_to_message:
        await message.reply_text('Reply To A Message To Encrypt It.')
        return
    text = message.reply_to_message.text
    text_in_bytes = bytes(text, 'utf-8')
    cipher_suite = Fernet(FERNET_ENCRYPTION_KEY)
    encrypted_text = cipher_suite.encrypt(text_in_bytes)
    bytes_in_text = encrypted_text.decode("utf-8")
    await message.reply_text(bytes_in_text)



@pyromode.on_message(filters.command(["decrypt", "dec"] & ~filters.edited)
@capture_err
async def decrypt(_, message: Message):
    if not message.reply_to_message:
        await message.reply_text('Reply To A Message To Decrypt It.')
        return
    text = message.reply_to_message.text
    text_in_bytes = bytes(text, 'utf-8')
    cipher_suite = Fernet(FERNET_ENCRYPTION_KEY)
    decoded_text = cipher_suite.decrypt(text_in_bytes)
    bytes_in_text = decoded_text.decode("utf-8")
    await message.reply_text(bytes_in_text)
