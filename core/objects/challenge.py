# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

from core.objects.hint import Hint
from core.objects.objective import Objective
from core.objects.flag import Flag, FLAG_ALREADY_CAPTURED, FLAG_CAPTURED_SUCCESSFULLY, FLAG_DOES_NOT_EXIST
from core.exceptions import ProviderNotFoundError, FlagNotFoundError, FlagAlreadyCapturedError, DuplicateFlagError,\
    ObjectiveAlreadyExists, HintNotFoundError, DuplicateHintError, HintMovementError

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
        self.hints = dict()
        self.objectives = dict()
        self.objective = None

    def __str__(self):
        return f"{self.name} on {self.provider}"

    def get_current_level(self):
        return self.level

    # region hints
    def _reorder_hints(self, levels: list = []):
        if not levels:
            levels = self.hints.keys()
        for level in levels:
            temp = list()
            for i, hint in enumerate(self.hints.get(level)):
                hint._order = i
                temp.append(hint)
            self.hints[level] = temp

    def create_hint(self, hint_text, level, cost):
        if level not in self.hints:
            self.hints[level] = list()
        try:
            hint = Hint(hint_text, level, cost)
            if hint in self.hints[level]:
                raise DuplicateHintError
            self.hints[level].append(hint)
            self._reorder_hints([level])
        except ValueError:
            raise

    def move_hint_up(self, level, index):
        if index == 0:
            raise HintMovementError
        try:
            lst = self.hints[level]
            lst.insert(index-1, lst.pop(index))
            self.hints[level] = lst
            self._reorder_hints([level])
        except (KeyError, IndexError, AttributeError):
            raise HintNotFoundError

    def move_hint_down(self, level, index):
        try:
            lst = self.hints[level]
            lst.insert(index, lst.pop(index+1))
            self.hints[level] = lst
            self._reorder_hints([level])
        except (KeyError, AttributeError):
            raise HintNotFoundError
        except IndexError:
            raise HintMovementError

    def delete_hint(self, level, index):
        try:
            self.hints[level].pop(index)
            self._reorder_hints([level])
        except (KeyError, IndexError, AttributeError):
            raise HintNotFoundError

    def get_hint_levels(self):
        return self.hints.keys()

    def get_hints(self, level):
        return self.hints.get(level, [])

    def reveal_next_hint(self):
        hints = self.get_hints(self.level)
        for index, hint in enumerate(hints):
            if not hint.revealed:
                hint.revealed = True
                self.hints[self.level][index] = hint
                return hint.text
        else:
            return "No hints are available for this level"
    # endregion hints

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
            flagobj.capture(username.lower())
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
                        self.update_objective(level)
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
            if flag.captured == username.lower():
                total += flag.value
        return total
    # endregion leaderboard

    # region objectives
    def create_objective(self, objective, level):
        if self.objectives.get(level):
            raise ObjectiveAlreadyExists
        self.objectives[level] = Objective(objective, level)

    def delete_objective(self, level):
        try:
            del self.objectives[level]
        except KeyError:
            pass

    def get_objectives(self):
        return sorted(self.objectives.values(), key=Objective.get_level)

    def get_current_objective(self):
        if self.objective:
            return self.objective
        try:
            return self.objectives.get(self.get_current_level()).text
        except AttributeError:
            return None

    def set_current_objective(self, text):
        """
        Overrides the current objective

        :param text: The objective text
        """
        self.objective = text

    def update_objective(self, level):
        while level >= 0:
            objective = self.objectives.get(level)
            if objective:
                self.objective = objective.text
                break
            level -= 1
    # endregion objectives
