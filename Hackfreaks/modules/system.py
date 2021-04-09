import speedtest
import psutil
import platform
from datetime import datetime
from platform import python_version, uname
from telegram import Update, Bot, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, __version__
from telegram.ext import run_async, CallbackQueryHandler, CommandHandler, CallBackContext

from Hackfreaks import dispatcher, DEV_USERS
from Hackfreaks.modules.disable import DisableAbleCommandHandler
from Hackfreaks.modules.helper_funcs.chat_status import dev_plus
from Hackfreaks.modules.helper_funcs.filters import CustomFilters

VERSION = "v0.2.3"

def convert(speed):
    return round(int(speed)/1048576, 2)

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor
	
@dev_plus
@run_async
def status(update: Update, context: CallbackContext):
        bot = context.bot
	chat = update.effective_chat
	
	stat = "*>-------< Basic >-------<*\n"
	stat += f"*Hackfreaks Version:* `{VERSION}`""\n"
	stat += f"*Python Version:* `"+python_version()+"`\n"
	uname = platform.uname()
	softw = "*>-------< Software >-------<*\n"
	softw += f"*System:* `{uname.system}`\n"
	softw += f"*Node Name:* `{uname.node}`\n"
	softw += f"*Release:* `{uname.release}`\n"
	softw += f"*Version:* `{uname.version}`\n"
	softw += f"*Machine:* `{uname.machine}`\n"
	softw += f"*Processor:* `{uname.processor}`\n"
	softw += "*Library Used:* `python-telegram-bot`\n"
	softw += "*Library version:* `" + str(__version__) + "`\n"
	boot_time_timestamp = psutil.boot_time()
	bt = datetime.fromtimestamp(boot_time_timestamp)
	softw += f"*Boot Time:* `{bt.day}`|`{bt.month}`|`{bt.year}` • `{bt.hour}H`:`{bt.minute}M`:`{bt.second}S`\n"
	cpuu = "*>-------< CPU >-------<*\n"
	cpuu += "*Physical cores:* `" + str(psutil.cpu_count(logical=False)) + "`\n"
	cpuu += "*Total cores:* `" + str(psutil.cpu_count(logical=True)) + "`\n"
	cpufreq = psutil.cpu_freq()
	cpuu += f"*Max Frequency:* `{cpufreq.max:.2f}Mhz`\n"
	cpuu += f"*Min Frequency:* `{cpufreq.min:.2f}Mhz`\n"
	cpuu += f"*Current Frequency:* `{cpufreq.current:.2f}Mhz`\n"
	for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
	    cpuu += f"*Core {i}:* `{percentage}%`\n"
	cpuu += f"*Total CPU Usage:* `{psutil.cpu_percent()}%`\n"
	svmem = psutil.virtual_memory()
	memm += "*>-------< Memory >-------<*"
	memm += f"*Total:* `{get_size(svmem.total)}`\n"
	memm += f"*Available:* `{get_size(svmem.available)}`\n"
	memm += f"*Used:* `{get_size(svmem.used)}`\n"
	memm += f"*Percentage:* `{svmem.percent}%`\n"
	disk = disk_usage("/")
	memm += "*Storage used:* " + str(disk[3]) + " %\n\n"
	reply = str(stat)+ str(softw) + str(cpuu) + str(memm) + "\n"
	bot.send_message(chat.id, reply, parse_mode=ParseMode.MARKDOWN)        

STATUS_HANDLER = CommandHandler("system", status, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(STATUS_HANDLER)

__command_list__ = ["system"]
__handlers__ = [STATUS_HANDLER]
