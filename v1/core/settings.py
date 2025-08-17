# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import logging

MAX_FREEBIES = 10
PRESS_DELAY = 50
DEFAULT_OBJECTIVE = "Escalate privileges in order to gain full control of the system"
DEFAULT_PROFILE = 3

STATE_MIDDLEWARE = 'core.state.filestore.FileStore'
# FILE_STORE_PATH = '.'

# Logging
LOG_FILE = 'twitchbot.log'
LOGGING_LEVEL = logging.DEBUG
