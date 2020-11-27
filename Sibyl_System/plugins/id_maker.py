from Sibyl_System import system_cmd, System
from PIL import Image, ImageDraw, ImageFont
import os

@System.on(system_cmd(pattern = r'get_id'))
async def image_maker(event) -> None:
     replied_user = await event.get_reply_message()
     #Download profile photo
     await System.download_profile_photo(replied_user.from_id, file= 'user.png', download_big = True)
     user_photo = Image.open('user.png')
     #open id photo
     id_template = Image.open('ID.png')
     #resize user photo to fit box in id template
     user_photo = user_photo.resize((1159, 1241))
     #put image in position
     id_template.paste(user_photo, (1003,641))
     #postion on where to draw text
     draw = ImageDraw.Draw(id_template)
     color = 'rgb(0, 0, 0)' #black
     font = ImageFont.truetype('font.ttf', size=80)
     font2 = ImageFont.truetype('font2.ttf', size=100)
     #put text in image
     draw.text((1000, 460), replied_user.sender.first_name.replace('\u2060', ''), fill=color, font=font2)
     draw.text((393, 50), str(replied_user.from_id), fill = color, font = font)
     id_template.save('user_id.png')
     if 'doc' in event.text:
         force_document = True
     else:
         force_document = False
     await System.send_message(
            event.chat_id,
            "Generated User ID",
            reply_to=event.message.id,
            file='user_id.png',
            force_document=force_document,
            silent=True
        )
     os.remove('user_id.png')
