# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

from core.objects.flag import Flag, FLAG_ALREADY_CAPTURED, FLAG_CAPTURED_SUCCESSFULLY, FLAG_DOES_NOT_EXIST
from core.exceptions import ProviderNotFoundError, FlagNotFoundError, FlagAlreadyCapturedError, DuplicateFlagError

PROVIDERS = ['virtualbox']


class Challenge:
    def __init__(self, id, provider, name):
        self.id = id
        if provider not in PROVIDERS:
            raise ProviderNotFoundError
        self.provider = provider
        self.name = name
        self.level = 0
        self.flags = dict()
        self.hints = set()
        self.objectives = set()
        self.objective = ''

    def __str__(self):
        return f"{self.name} on {self.provider}"

    def get_current_level(self):
        return self.level

    def get_current_objective(self):
        return self.objective

    def reveal_next_hint(self):
        if not self.hints:
            return "No hints available at this time"
        else:
            # TODO: Filter for current level
            #       Exclude already revealed hints
            #       Return the first applicable one and mark it as revealed
            return self.hints[0]

    # region flags
    def create_flag(self, flag_text, level, points_value, description=None, location=None):
        if self.flags.get(flag_text):
            raise DuplicateFlagError
        flag = Flag(flag_text, level, points_value, description=description, location=location)
        self.flags[flag.text] = flag

    def delete_flag(self, flag_text):
        try:
            del self.flags[flag_text]
        except KeyError:
            raise FlagNotFoundError

    def get_flag(self, flag):
        flagobj = self.flags.get(flag)
        if not flagobj:
            raise FlagNotFoundError
        return flagobj

    def get_flags(self):
        return sorted(self.flags.values(), key=Flag.get_level)

    def set_flag(self, flag):
        self.flags[flag.text] = flag

    def _submit_flag(self, username, flag):
        try:
            flagobj = self.get_flag(flag)
            flagobj.capture(username)
            self.flags[flagobj.text] = flagobj
            return flagobj
        except AttributeError:
            raise FlagNotFoundError
        except (FlagNotFoundError, FlagAlreadyCapturedError):
            raise

    def validate_flag(self, username, text):
        for flag in self.flags.keys():
            if flag in text:  # FIXME: Should probably be a bit more picky on the syntax
                try:
                    flagobj = self._submit_flag(username, flag)
                    level = flagobj.get_level()
                    if self.level < level:
                        self.level = level
                    points = flagobj.get_value()
                    return (FLAG_CAPTURED_SUCCESSFULLY, points)
                except FlagAlreadyCapturedError:
                    return (FLAG_ALREADY_CAPTURED, None)
                except FlagNotFoundError:
                    continue
        return (FLAG_DOES_NOT_EXIST, None)
    # endregion flags

    # region leaderboard
    def get_challenge_points(self, username):
        total = 0
        for flag in self.flags.values():
            if flag.captured == username:
                total += flag.value
        return total
    # endregion leaderboard
