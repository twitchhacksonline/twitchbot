# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import time
from core.exceptions import FlagAlreadyCapturedError

FLAG_DOES_NOT_EXIST = -1
FLAG_ALREADY_CAPTURED = 0
FLAG_CAPTURED_SUCCESSFULLY = 1


class Flag:
    def __init__(self, flag_text, level, points_value, description=None, location=None):
        """
        Flag located on a challenge

        :param flag_text: The actual flag text
        :param level: The level which this flag unlocks
        :param points_value: The amount of points awarded for capturing the flag
        :param description: (optional) Description on how to find/reveal the flag
        :param location: (optional) Where the flag is located in the challenge

        """
        self.text = flag_text
        try:
            self.level = int(level)
            self.value = int(points_value)
        except ValueError:
            raise
        self.description = description
        self.location = location
        self.captured = None
        self.capture_time = None

    def __str__(self):
        spacing = " "*(60 - len(self.text))
        text = f"Flag: {self.text}{spacing}Level: {self.level}\tPoints value: {self.value}"
        if self.captured:
            text += f"  \tCaptured by: {self.captured}"
        else:
            text += "  \tNot captured"
        return text

    def is_captured(self):
        return self.captured is not None

    def capture(self, username):
        if self.is_captured():
            raise FlagAlreadyCapturedError
        else:
            self.captured = username
            self.capture_time = int(time.time())

    def get_value(self):
        return self.value

    def get_level(self):
        return self.level
