# squireBot.py
import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from Tournament import *

from baseBot import *
from adminCommands import *
from playerCommands import *
from judgeCommands import *


bot.run(TOKEN)

