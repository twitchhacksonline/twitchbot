# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo


class AbstractStore:
    def __init__(self):
        pass

    def create_profile(self, channel, bot=None, discard=False):
        """
        Create/Initialize a new profile

        :param channel: The channel name
        :param bot: (optional) The bot username
        :param discard: (optional) Discard any unsaved data in the existing profile
        :return: Newly created profile
        :rtype: core.objects.Profile
        """
        raise NotImplementedError

    def load_profile(self, id=None):
        """
        Load an existing profile from disk

        :return: The loaded profile object
        :rtype: core.object.Profile
        :raises ProfileNotFoundError: Profile does not exist
        """
        raise NotImplementedError

    def save_profile(self):
        """
        Save the current profile to disk

        :return: Profile saved successfully
        :rtype: Boolean
        """
        raise NotImplementedError

    def create_challenge(self, provider, name):
        """
        Create a new challenge configuration

        :return: The new challenge object
        :rtype: core.object.Challenge
        """
        raise NotImplementedError

    def load_challenge(self):
        """
        Load an existing challenge from disk

        :return: The loaded challenge object
        :rtype: core.object.Challenge
        :raises ChallengeNotFoundError: Challenge is not selected, or challenge does not exist
        """
        raise NotImplementedError

    def save_challenge(self):
        """
        Save the current challenge to disk

        :return: Challenge saved successfully
        :rtype: Boolean
        :raise ChallengeNotFoundError: No selected challenge
        """
        raise NotImplementedError

    def get_allowed_users(self):
        """
        Fetch the list of allowed users

        :return: Usernames that are allowed to interact
        :rtype: list of strings
        """
        raise NotImplementedError

    def set_allowed_users(self, usernames):
        """
        Update the list of allowed users

        :param usernames: list of usernames as string
        :return: Saved successfully
        :rtype: Boolean
        """
        raise NotImplementedError

    def get_denied_users(self):
        """
        Fetch the list of denied users

        :return: Usernames that are not allowed to interact
        :rtype: list of strings
        """
        raise NotImplementedError

    def set_denied_users(self, usernames):
        """
        Update the list of denied users

        :param usernames: list of usernames as string
        :return: Saved successfully
        :rtype: Boolean
        """
        raise NotImplementedError

    def update_user(self, user):
        """
        Update a user

        :param user: User object or username
        :return: Updated successfully
        :rtype: Boolean
        """
        raise NotImplementedError

    def save_interaction(self, interaction):
        """
        Save a new interaction

        :param interaction: New interaction object
        :return: Saved successfully
        :rtype: Boolean
        """
        raise NotImplementedError

    def cheered(self, username, channel, amount, message):
        raise NotImplementedError

    def subscribed(self, username, channel, message):
        raise NotImplementedError

    def spent_channel_points(self, username, channel, amount, reward):
        raise NotImplementedError

    def flag_submit(self, username, challenge, flag):
        raise NotImplementedError

    def set_stream_state(self, profile, stream_state):
        raise NotImplementedError

    def set_challenge_state(self, profile, challenge, state):
        raise NotImplementedError
