import re
from os import environ

id_pattern = re.compile(r'^.\d+$')
def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

# Bot information
SESSION = environ.get('SESSION', 'Manual_Filter_Bot')
API_ID = int(environ.get('API_ID', ''))
API_HASH = environ.get('API_HASH', '')
BOT_TOKEN = environ.get('BOT_TOKEN', '')

# Bot Admins
ADMINS = [int(admins) if id_pattern.search(admins) else admins for admins in environ.get('ADMINS', '').split()]

# Channels
auth_channel = environ.get('AUTH_CHANNEL', '')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', ''))

# Support Group
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'https://t.me/Hansaka_Anuhas')

# MongoDB information
DATABASE_URL = environ.get('DATABASE_URL', "")
DATABASE_NAME = environ.get('DATABASE_NAME', "Cluster0")

# Bot settings
MANUAL_FILTER = is_enabled((environ.get('MANUAL_FILTER', "True")), True)

# Log
LOG_STR = ("MANUAL_FILTER are enabled." if MANUAL_FILTER else "MANUAL_FILTER are disabled.")
