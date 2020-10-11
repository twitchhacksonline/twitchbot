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


class FlagNotFoundError(IndexError):
    """The flag does not exist"""
    pass
