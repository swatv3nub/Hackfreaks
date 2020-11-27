from Sibyl_System import system_cmd, System
import asyncio
import io

@System.on(system_cmd("(term|terminal|sh|shell) "))
async def shell(event):
  if event.fwd_from: return
  cmd = event.text.split(" ", 1)
  if len(cmd) == 1: return
  else: cmd = cmd[1]
  async_process =  await asyncio.create_subprocess_shell(cmd, 
  stdout=asyncio.subprocess.PIPE, 
  stderr=asyncio.subprocess.PIPE
  )
  stdout, stderr = await async_process.communicate()
  msg = ""
  if stderr.decode(): msg += f"**Stderr:**\n`{stderr.decode()}`"
  if stdout.decode(): msg += f"**Stdout:**\n`{stdout.decode()}`"
  if len(msg) > 4096:
    with io.BytesIO(msg) as file:
      file.name = "shell.txt"
      await System.send_file(
        event.chat.id,
        file,
        force_document = True,
        caption = "Output was too long, Sending as file",
        reply_to = event.message.id
      )
      return
  await event.reply(msg)


__plugin_name__ = "shell"

help_plus = """
Cmd - sh or shell or term or terminal
Example - `?sh echo owo`
Output - owo
"""
