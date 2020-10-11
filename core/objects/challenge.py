# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

from core.exceptions import ProviderNotFoundError, FlagNotFoundError

PROVIDERS = ['virtualbox']
FLAG_DOES_NOT_EXIST = -1
FLAG_ALREADY_CAPTURED = 0
FLAG_CAPTURED_SUCCESSFULLY = 1


class Challenge:
    def __init__(self, id, provider, name):
        self.id = id
        if provider not in PROVIDERS:
            raise ProviderNotFoundError
        self.provider = provider
        self.name = name
        # TODO: Make the flag/hint/level/objective system
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

    def get_flag(self, flag):
        flagobj = self.flags.get(flag)
        if not flagobj:
            raise FlagNotFoundError
        return flagobj

    def submit_flag(self, username, flag):
        try:
            flagobj = self.get_flag(flag)
            if flagobj.submitted:
                return False
            else:
                flagobj.submitted = username
                return True
        except (FlagNotFoundError, AttributeError):
            return False

    def validate_flag(self, username, submitted):
        for flag in self.flags.keys():
            if flag in submitted:  # FIXME: Should probably be a bit more picky on the syntax
                success = self.submit_flag(username, flag)
                return FLAG_CAPTURED_SUCCESSFULLY if success else FLAG_ALREADY_CAPTURED
        return FLAG_DOES_NOT_EXIST
