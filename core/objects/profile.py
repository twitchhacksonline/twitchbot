# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import logging
from core.objects.user import User

logger = logging.getLogger(__name__)


class Profile:
    def __init__(self, id, channel, bot=None, client_id=None):
        """
        Twitch channel and API profile

        :param id: Integer id for the profile
        :param channel: The twitch channel name
        :param bot: The nick for the twitch bot (optional)
        :param client_id: The Twitch Application Client ID for making API requests
        """
        self.id = id
        self.channel_name = channel
        self.bot_name = None
        self.superusers = set([channel])
        if bot and bot != channel:
            self.bot_name = bot
            self.superusers.add(bot)
        self.users = dict()
        # Twitch application (API)
        self.client_id = client_id
        self.tokens = dict()
        self.api_token = None
        self.irc_token = None
        self.bot_id = None
        self.channel_id = None
        # Current selected challenge
        self.challenge = None
        # Discord link
        self.discord = None

    def __str__(self):
        if self.bot_name:
            return f'{self.bot_name} on {self.channel_name}'
        return self.channel_name

    def fetch_data(self):
        """
        Fetch any missing values that can be collected from Twitch API
        Using self.client_id
        """
        pass

    def add_new_user(self, user):
        """
        Add a new user to the user database

        :param user: TwitchIO user object
        """
        superuser = user.name in self.superusers
        moderator = user.is_mod
        self.users[user.name] = User(user.name, superuser=superuser, moderator=moderator,
                                     client_id=self.client_id, channel_id=self.channel_id)

    def set_allowed_users(self, usernames):
        """
        Update the list of allowed users

        :param usernames: list of usernames
        """
        logger.debug("Allowing users: %s", usernames)
        for username in usernames:
            username = username.lower()
            user = self.users.get(username)
            if user:
                if not user.interact:
                    user.interact = True
                    self.users[username] = user
            else:
                new_user = User(username, client_id=self.client_id, channel_id=self.channel_id)
                new_user.interact = True
                self.users[username] = new_user
        logger.info("Added %s to allow list", usernames)

    def set_denied_users(self, usernames):
        """
        Update the list of denied users

        :param usernames: list of usernames
        """
        logger.debug("Denying users: %s", usernames)
        for username in usernames:
            username = username.lower()
            user = self.users.get(username)
            if user:
                if user.interact or user.interact is None:
                    user.interact = False
                    self.users[username] = user
            else:
                new_user = User(username, client_id=self.client_id, channel_id=self.channel_id)
                new_user.interact = False
                self.users[username] = new_user
        logger.info("Added %s to deny list", usernames)

    def reset_interact(self, usernames):
        """
        Resets allowed/denied users to default

        :param usernames: list of usernames
        """
        logger.debug("Resetting interact on users: %s", usernames)
        for username in usernames:
            username = username.lower()
            user = self.users.get(username)
            if user:
                user.interact = None
                self.users[username] = user
            else:
                new_user = User(username, client_id=self.client_id, channel_id=self.channel_id)
                self.users[user] = new_user
        logger.info("Reset interact property for: %s", usernames)
