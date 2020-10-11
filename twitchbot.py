#!/usr/bin/env python3
#
# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import sys
import logging
from core.state import State
from core.interactive import Interactive
from core.settings import LOG_FILE, LOGGING_LEVEL


logging.basicConfig(filename=LOG_FILE, level=LOGGING_LEVEL)
logger = logging.getLogger(__name__)


def main():
    state = State()
    console = Interactive(state)
    console.cmdloop()
    return True


if __name__ == '__main__':
    exit_state = main()
    if exit_state:
        sys.exit(0)
