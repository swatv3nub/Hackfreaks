import sys
from Sibyl_System import system_cmd, System
from io import StringIO
import traceback
import inspect
#Thanks to stackoverflow for existing https://stackoverflow.com/questions/3906232/python-get-the-print-output-in-an-exec-statement


@System.on(system_cmd(pattern = r"sibyl (exec|execute|x|ex)"))
async def run(event):
  code = event.text.split(" ", 2)
  if len(code) == 2: return
  stderr, output, wizardry = None, None, None
  code = code[2]
  old_stdout = sys.stdout
  old_stderr = sys.stderr
  redirected_output = sys.stdout = StringIO()
  redirected_error = sys.stderr = StringIO()
  try:
    await async_exec(code, event)
  except Exception:
    wizardry = traceback.format_exc()
  output = redirected_output.getvalue()
  stderr = redirected_error.getvalue()
  sys.stdout = old_stdout
  sys.stderr = old_stderr
  if wizardry: final = "**Output**:\n`" + wizardry
  elif output: final = "**Output**:\n`" + output
  elif stderr: final = "**Output**:\n`" + stderr
  else: final = "`OwO no output"
  if len(final) > 4096:
    with open('exec.txt', 'w+', encoding="utf-8") as f:
      f.write(final)
    await System.send_file(event.chat_id, 'exec.txt')
    return
  await event.reply(final + '`' )

@System.on(system_cmd(pattern = r"sibyl (ev|eva|eval|py)"))
async def run_eval(event):
  cmd = event.text.split(' ' , 2)
  cmd = cmd[2] if len(cmd) > 2 else ""
  try:
     evaluation = eval(cmd)
     if inspect.isawaitable(evaluation):
       evaluation = await evaluation
  except (Exception) as e: 
       evaluation = str(e)
  await event.reply(f'Output:\n`{evaluation}`')
  


async def async_exec(code, event):
    exec(
        f'async def __async_exec(event): ' +
        ''.join(f'\n {l}' for l in code.split('\n'))
    )
    return await locals()['__async_exec'](event)


__plugin_name__ = "py"

help_plus = """
Run code using **exec** 
CMD - <x or ex or exec or execute> your code here
EXAMPLE - `!sibyl x print("OWO")`
Run code using **eval**
CMD - <ev or eva or eval or py> your code
EXAMPLE - `!sibyl eval 1 + 1`
"""
