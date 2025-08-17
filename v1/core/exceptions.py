# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

class ProviderNotFoundError(Exception):
    """The selected provider does not exist"""
    pass


class ProfileNotFoundError(FileNotFoundError):
    """The requested challenge does not exist"""
    pass


class NoProfileSelectedError(Exception):
    """No profile has been loaded"""
    pass


class ChallengeNotFoundError(FileNotFoundError):
    """The requested challenge does not exist"""
    pass


class NoChallengeSelectedError(Exception):
    """No challenge has been loaded"""
    pass


class BoxNotInitializedError(Exception):
    """Box has not been initialized yet"""
    pass


class BoxNotRunningError(Exception):
    """Box is not running and can't be interacted with"""
    pass


class BoxAlreadyRunningError(Exception):
    """Box is already running"""
    pass


class BoxNotFoundError(FileNotFoundError):
    """The requested box does not exist"""
    pass


class DuplicateFlagError(IndexError):
    """The flag already exists"""
    pass


class FlagNotFoundError(IndexError):
    """The flag does not exist"""
    pass


class FlagAlreadyCapturedError(Exception):
    """The flag has already been captured"""
    pass


class ObjectiveAlreadyExists(IndexError):
    """The objective has already been set"""
    pass


class HintNotFoundError(IndexError):
    """The hint does not exist"""
    pass


class DuplicateHintError(IndexError):
    """The hint already exists"""
    pass


class HintMovementError(IndexError):
    """The hint can not be moved in that direction"""
    pass
