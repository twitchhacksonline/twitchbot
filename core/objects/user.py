# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

from core import settings


class ExtraUserInfo:
    def __init__(self, superuser, moderator):
        self.user_id = 0
        self.superuser = superuser
        self.moderator = moderator
        self.following = False
        self.subscribed = 0
        self.cheered = 0


class User:
    def __init__(self, name, superuser=False, moderator=False, client_id=None, channel_id=None):
        self.name = name
        self.interact = None
        self.interaction_count = 0
        self.team = None
        self.extra = ExtraUserInfo(superuser, moderator)
        if client_id and channel_id:
            self.fetch_data(client_id, channel_id)

    def __str__(self):
        if self.extra:
            if self.extra.superuser:
                return f"Superuser: {self.name}"
            elif self.extra.moderator:
                return f"Moderator: {self.name}"
        else:
            return self.name

    def fetch_data(self, client_id, channel_id):
        """
        Fetch extra data from Twitch API using client_id
        """
        # Candidates:
        # self.extra.user_id
        # self.extra.subscribed (Total months subscribed)
        # self.extra.cheered (Total amount cheered)
        # self.extra.moderator (Is user a moderator in profile channel)

    def can_interact(self):
        if self.extra and (self.extra.superuser or self.extra.moderator):
            return (True, None)
        if self.interact is False:
            return (False, None)
        if self.interact:
            return (True, None)
        limited_freebies = hasattr(settings, 'MAX_FREEBIES') and settings.MAX_FREEBIES > 0
        if not limited_freebies:
            return (True, None)
        return (self.interaction_count <= limited_freebies,
                f"{self.name}: Please follow the channel to continue interacting!")
