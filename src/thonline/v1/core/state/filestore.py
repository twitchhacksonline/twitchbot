# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import os
import pickle
import logging
from pathlib import Path
from core import settings
from core.objects.profile import Profile
from core.objects.challenge import Challenge
from core.objects.user import User
from core.exceptions import ChallengeNotFoundError, ProfileNotFoundError
from core.state.store import AbstractStore

logger = logging.getLogger(__name__)


def get_full_path(filename):
    path = Path.home() / '.config' / 'twitchbot'
    if hasattr(settings, 'FILE_STORE_PATH') and settings.FILE_STORE_PATH:
        path = Path(settings.FILE_STORE_PATH)
    if not path.exists():
        logger.debug(f"{path} does not exist, creating..")
        path.mkdir()
    if filename:
        return path / filename
    return path


def get_next_available_id(type):
    all_files = os.listdir(get_full_path(None))
    used_ids = []
    for filename in all_files:
        if not filename.endswith('.'+type):
            continue
        try:
            used_ids.append(int(filename[:3]))
        except ValueError:
            continue
    if not used_ids:
        return 1
    return max(used_ids) + 1


class FileStore(AbstractStore):
    """
    Store the profiles and challenges as files
    Uses location ~/.config/twitchbot if there is no settings.FILE_STORE_PATH
    """
    def __init__(self):
        self._profile = None

    def _get_filename_by_id(self, id, type):
        all_files = os.listdir(get_full_path(None))
        for filename in all_files:
            try:
                if id == int(filename[:3]) and filename.endswith(type):
                    return filename
            except ValueError:
                continue
        return None

    def _generate_new_filename(self, obj):
        if isinstance(obj, Profile):
            if obj.bot_name:
                return f"{obj.id:03}_{obj.bot_name}_{obj.channel_name}.profile"
            else:
                return f"{obj.id:03}_{obj.channel_name}.profile"
        elif isinstance(obj, Challenge):
            return f"{obj.id:03}_{obj.provider}_{obj.name}.challenge"
        else:
            raise TypeError

    def _save_object(self, obj, new=False):
        """
        Save a challenge or profile object to disk
        """
        path = None
        if new:
            path = get_full_path(self._generate_new_filename(obj))
        else:
            if isinstance(obj, Profile):
                path = get_full_path(self._get_filename_by_id(obj.id, 'profile'))
            elif isinstance(obj, Challenge):
                path = get_full_path(self._get_filename_by_id(obj.id, 'challenge'))
            else:
                raise TypeError
        try:
            with path.open('wb') as f:
                pickle.dump(obj, f)
        except (TypeError, FileNotFoundError, IsADirectoryError, PermissionError):
            raise

    def _load_object(self, id, type):
        """
        Load a challenge or profile object from disk
        """
        filename = self._get_filename_by_id(id, type)
        if not filename:
            logger.error("Could not resolve filename of %s with id %s", type, id)
            raise FileNotFoundError
        path = get_full_path(filename)
        try:
            with path.open('rb') as f:
                obj = pickle.load(f)
        except (TypeError, FileNotFoundError, IsADirectoryError, PermissionError):
            raise
        return obj

    def create_profile(self, channel, bot=None, client_id=None):
        """
        Create/Initialize a new profile

        :parap client_id: The client_id to use for API requests
        :param channel: The channel name
        :param bot: (optional) The bot username
        :return: Newly created profile
        :rtype: core.objects.Profile
        """
        profile = Profile(get_next_available_id('profile'), channel, bot=bot, client_id=client_id)
        if self.save_profile(profile, new=True):
            logger.info("New profile created: %s", profile)
            self._profile = profile
        else:
            profile = None
        return profile

    def load_profile(self, id=None):
        """
        Load an existing profile from disk

        :return: The loaded profile object
        :rtype: core.object.Profile
        :raises ProfileNotFoundError: Profile does not exist
        """
        try:
            obj = self._load_object(id, 'profile')
            self._profile = obj
            return obj
        except (TypeError, PermissionError, FileNotFoundError, IsADirectoryError) as e:
            logger.error("Profile file could not be loaded %s", e)
            raise ProfileNotFoundError

    def save_profile(self, profile, new=False):
        """
        Save a profile to disk

        :return: Profile saved successfully
        :rtype: Boolean
        """
        try:
            self._profile = profile
            self._save_object(profile, new)
        except (TypeError, PermissionError, FileNotFoundError, IsADirectoryError) as e:
            logger.error("Profile file storage error: %s", e)
            return False
        return True

    def create_challenge(self, provider, name):
        """
        Create a new challenge configuration

        :return: The new challenge object
        :rtype: core.object.Challenge
        """
        challenge = Challenge(get_next_available_id('challenge'), provider, name)
        if self.save_challenge(challenge, new=True):
            logger.info("New challenge created: %s", challenge)
        else:
            challenge = None
        return challenge

    def load_challenge(self, id):
        """
        Load an existing challenge from disk

        :return: The loaded challenge object
        :rtype: core.object.Challenge
        :raises ChallengeNotFoundError: Challenge is not selected, or challenge does not exist
        """
        try:
            obj = self._load_object(id, 'challenge')
            return obj
        except (TypeError, PermissionError, FileNotFoundError, IsADirectoryError) as e:
            logger.error("Challenge file could not be loaded %s", e)
            raise ChallengeNotFoundError

    def save_challenge(self, challenge, new=False):
        """
        Save a challenge to disk

        :return: Challenge saved successfully
        :rtype: Boolean
        """
        try:
            self._save_object(challenge, new)
        except (TypeError, PermissionError, FileNotFoundError, IsADirectoryError) as e:
            logger.error("Challenge file storage error: %s", e)
            return False
        return True

    def get_allowed_users(self, profile_id):
        """
        Fetch the list of allowed users

        :param profile_id: Profile to load users from
        :return: Usernames that are allowed to interact
        :rtype: list of strings
        """
        if self._profile.id == profile_id:
            profile = self._profile
        else:
            profile = self.load_profile(profile_id)
        return [user.name for user in profile.users.values() if user.can_interact()]

    def set_allowed_users(self, profile_id, usernames):
        """
        Update the list of allowed users

        :param profile_id: Profile id to save users to
        :param usernames: list of usernames as string
        :return: Saved successfully
        :rtype: Boolean
        """
        if self._profile.id == profile_id:
            profile = self._profile
        else:
            profile = self.load_profile(profile_id)
        existing_users = profile.users.keys()
        for user in usernames:
            if user in existing_users:
                value = profile.users.get(user)
                if not value.interact:
                    value.interact = True
                    profile.users[user] = value
            else:
                new_user = User(user)
                new_user.interact = True
                profile.users[user] = new_user
        return self.save_profile(profile)

    def get_denied_users(self, profile_id):
        """
        Fetch the list of denied users

        :param profile_id: Profile to load users from
        :return: Usernames that are not allowed to interact
        :rtype: list of strings
        """
        if self._profile.id == profile_id:
            profile = self._profile
        else:
            profile = self.load_profile(profile_id)
        return [user.name for user in profile.users.values() if not user.can_interact()]

    def set_denied_users(self, profile_id, usernames):
        """
        Update the list of denied users

        :param profile_id: Profile id to save users to
        :param usernames: list of usernames as string
        :return: Saved successfully
        :rtype: Boolean
        """
        if self._profile.id == profile_id:
            profile = self._profile
        else:
            profile = self.load_profile(profile_id)
        existing_users = profile.users.keys()
        for user in usernames:
            if user in existing_users:
                value = profile.users.get(user)
                if value.interact or value.interact is None:
                    value.interact = False
                    profile.users[user] = value
            else:
                new_user = User(user)
                new_user.interact = False
                profile.users[user] = new_user
        return self.save_profile(profile)

    def update_user(self, user):
        """
        Update a user

        :param user: User object or username
        :return: Updated successfully
        :rtype: Boolean
        """
        # TODO: Implement this
        return True

    def save_interaction(self, interaction):
        """
        Save a new interaction

        :param interaction: New interaction object
        :return: Saved successfully
        :rtype: Boolean
        """
        # Interactions are not saved to disk
        return True
