# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import time
import logging
from importlib import import_module
from core import settings
from core.vm.virtualbox import VirtualBoxSrv
from core.objects.flag import FLAG_CAPTURED_SUCCESSFULLY
from bots.twitch import TwitchBot
from core.exceptions import ProfileNotFoundError, ChallengeNotFoundError,\
    NoProfileSelectedError, NoChallengeSelectedError, BoxNotInitializedError,\
    BoxNotRunningError, BoxAlreadyRunningError, DuplicateFlagError, FlagNotFoundError

logger = logging.getLogger(__name__)
IRC_SCOPE = ["channel:moderate", "channel_editor", "chat:edit", "chat:read", "whispers:edit", "whispers:read"]
API_SCOPE = ["bits:read", "channel:moderate", "channel:read:redemptions", "channel:read:subscriptions",
             "channel_subscriptions", "chat:edit", "chat:read", "clips:edit", "moderation:read",
             "user:edit:broadcast", "whispers:edit", "whispers:read"]


class State:
    def __init__(self):
        self.profile = None
        self.challenge = None
        self.twitchbot = None
        self.hotseat = None
        self.hotseat_expiry = None
        self.box = None
        self.press_delay = 0
        if hasattr(settings, 'PRESS_DELAY') and settings.PRESS_DELAY:
            self.press_delay = settings.PRESS_DELAY
        # Load values from the selected state store
        self.load_store(settings.STATE_MIDDLEWARE)

    def load_store(self, middleware):
        parts = middleware.split('.')
        module_path = '.'.join(parts[:-1])
        klass = parts[-1]
        module = import_module(module_path)  # noqa: F841
        self.store = eval(f'module.{klass}')()
        if hasattr(settings, 'DEFAULT_PROFILE') and settings.DEFAULT_PROFILE:
            profile_id = settings.DEFAULT_PROFILE
            try:
                self.load_profile(profile_id)
            except ProfileNotFoundError:
                logger.error("The default profile does not exist")

    def cleanup(self, discard=False):
        if self.box:
            self.box.cleanup()
        if self.challenge:
            if not discard:
                self.store.save_challenge(self.challenge)
            self.challenge = None
        if self.profile:
            self.disconnect_twitch()
            if not discard:
                self.store.save_profile(self.profile)
            self.profile = None

    def get_status(self):
        if not self.profile:
            return "Profile has not been loaded"
        elif self.profile and not self.twitchbot:
            return f"Profile: '{self.profile}'\n{self.challenge_status()}"
        else:
            return f"Profile: '{self.profile}'\n{self.challenge_status()}\n{self.twitchbot_status()}"

    # region profile
    def create_profile(self, channel_name, bot_name=None, client_id=None, select=False):
        if not client_id and hasattr(settings, 'CLIENT_ID'):
            client_id = settings.CLIENT_ID
        profile = self.store.create_profile(channel_name, bot=bot_name, client_id=client_id)
        if select:
            self.load_profile(profile.id)
        return profile

    def load_profile(self, profile_id, discard=False):
        if self.profile:
            self.cleanup(discard)
        self.profile = self.store.load_profile(profile_id)
        if not self.profile:
            raise ProfileNotFoundError
        expired = self.verify_tokens()
        if expired:
            self.renew_tokens(expired)
        if self.profile.challenge:
            try:
                self.load_challenge(self.profile.challenge)
            except ChallengeNotFoundError:
                self.profile.challenge = None
        logger.info("Profile %s has been loaded", self.profile)
        return self.profile

    def save_profile(self):
        if not self.profile:
            raise NoProfileSelectedError
        if self.store:
            self.store.save_profile(self.profile)

    def _verify_token(self, client_id, token):
        # TODO: Do the actual request
        return True

    def verify_tokens(self):
        if not self.profile:
            raise NoProfileSelectedError
        expired = []
        if self.profile.api_token:
            if not self._verify_token(self.profile.client_id, self.profile.api_token):
                expired.append("api")
        if self.profile.irc_token:
            if not self._verify_token(self.profile.client_id, self.profile.irc_token):
                expired.append("irc")
        return expired

    def _renew_token(self, client_id, scope):
        pass

    def renew_tokens(self, *args):
        pass

    def new_interaction(self, interaction):
        pass

    def new_subscription(self, username, total_months):
        pass

    def user_cheered(self, username, amount):
        pass

    def set_hotseat(self, username, seconds=None):
        if username and username.startswith('@'):
            username = username[1:]
        self.hotseat = username
        try:
            self.hotseat_expiry = int(time.time()) + seconds
        except TypeError:
            self.hotseat_expiry = None
        if username and seconds:
            logger.debug("%s has been awarded the hotseat for %s seconds", username, seconds)
        elif username:
            logger.debug("%s has been awarded the hotseat", username)
        else:
            logger.debug("Hotseat has been cleared")

    def get_hotseat(self):
        if self.hotseat:
            if not self.hotseat_expiry:
                logger.debug("%s has the hotseat", self.hotseat)
            elif self.hotseat_expiry >= int(time.time()):
                seconds = self.hotseat_expiry - int(time.time())
                logger.debug("%s has the hotseat for another %s seconds", self.hotseat, seconds)
            else:
                logger.debug("Hotseat has expired, clearing it..")
                self.hotseat = None
        return self.hotseat

    def allow_users(self, users):
        if not self.profile:
            raise NoProfileSelectedError
        self.profile.set_allowed_users(users)

    def deny_users(self, users):
        if not self.profile:
            raise NoProfileSelectedError
        self.profile.set_denied_users(users)

    def reset_users(self, users):
        if not self.profile:
            raise NoProfileSelectedError
        self.profile.reset_users(users)

    def allow_interaction(self, user):
        if not self.profile:
            raise NoProfileSelectedError
        username = user.name
        hotseat = self.get_hotseat()
        if username not in self.profile.users.keys():
            self.profile.add_new_user(user)
        if username in self.profile.superusers or user.is_mod:
            return (True, None)
        elif hotseat and username != hotseat.lower():
            return (False, f"Can't interact while {hotseat} is in the hotseat!")
        elif username in self.profile.users:
            return self.profile.users[username].can_interact()

    def get_channel_point_rewards(self):
        # Can we fetch this from Twitch API?
        pass

    def redeemed_channel_points(self, username, points, reward):
        # Have a predefined list of rewards
        # TODO: Make methods for handling each of the separate rewards
        # MAYBE: Use API to mark redemption as completed/rejected
        pass

    def get_press_delay(self):
        if not self.box:
            raise BoxNotInitializedError
        return self.box.get_delay()

    def set_press_delay(self, delay, expiration=None):
        if not self.box:
            raise BoxNotInitializedError
        self.box.set_delay(delay, expiration=expiration)
    # endregion profile

    # region challenge
    def create_challenge(self, provider, name, select=False):
        if select and not self.profile:
            raise NoProfileSelectedError
        challenge = self.store.create_challenge(provider, name)
        if select and challenge:
            return self.select_challenge(challenge.id)
        return challenge

    def load_challenge(self, challenge_id):
        self.challenge = self.store.load_challenge(challenge_id)
        self.initialize_box()
        if self.twitchbot:
            # TODO: Update the channel description
            pass
        return self.challenge

    def save_challenge(self):
        self.store.save_challenge(self.challenge)

    def select_challenge(self, challenge_id):
        if not self.profile:
            raise NoProfileSelectedError
        try:
            challenge = self.load_challenge(challenge_id)
            self.profile.challenge = challenge.id
            logger.info("Profile '%s' is now using challenge '%s'", self.profile, challenge)
        except ChallengeNotFoundError:
            return None
        return challenge

    def initialize_box(self):
        if self.box:
            self.box.cleanup()
            self.box = None
        if not self.challenge:
            raise NoChallengeSelectedError
        try:
            self.box = VirtualBoxSrv(self.challenge.name, self.press_delay)
        except ChallengeNotFoundError:
            logger.error("The challenge '%s' is not configured correctly. VM client not found", self.challenge)
            self.box = None

    def challenge_status(self):
        if not self.profile or not self.profile.challenge:
            return "No challenge selected"
        elif not self.challenge:
            return "Challenge not loaded"
        elif not self.box:
            return f"Challenge '{self.challenge.name}' not initialized"
        elif self.box.is_running():
            return f"Challenge '{self.challenge.name}' is running"
        else:
            return f"Challenge '{self.challenge.name}' is not running"

    def start_challenge(self, restore=False):
        if not self.challenge:
            raise NoChallengeSelectedError
        if not self.box:
            raise BoxNotInitializedError
        try:
            if restore:
                self.box.restore()
            self.box.launch()
        except BoxAlreadyRunningError:
            pass

    def snapshot_challenge(self, username):
        if not self.challenge:
            raise NoChallengeSelectedError
        if not self.box:
            raise BoxNotInitializedError
        self.box.snapshot(username)

    def stop_challenge(self, save=True):
        if not self.challenge:
            raise NoChallengeSelectedError
        if not self.box:
            raise BoxNotInitializedError
        try:
            self.box.shut_down(save)
        except BoxNotRunningError:
            pass

    def get_special_keys(self):
        if not self.challenge:
            raise NoChallengeSelectedError
        if not self.box:
            raise BoxNotInitializedError
        return self.box.get_special_keys()

    def send_keys(self, keys):
        if not self.challenge:
            raise NoChallengeSelectedError
        if not self.box:
            raise BoxNotInitializedError
        try:
            return self.box.send(keys)
        except BoxNotRunningError:
            raise

    def type_text(self, text):
        if not self.challenge:
            raise NoChallengeSelectedError
        if not self.box:
            raise BoxNotInitializedError
        try:
            return self.box.type(text)
        except BoxNotRunningError:
            raise

    def release_keys(self):
        if not self.challenge:
            raise NoChallengeSelectedError
        if not self.box:
            raise BoxNotInitializedError
        try:
            self.box.release()
        except BoxNotRunningError:
            raise

    def create_flag(self, flag_text, level, points_value, description=None, location=None):
        if not self.challenge:
            raise NoChallengeSelectedError
        try:
            self.challenge.create_flag(flag_text, level, points_value, description=description, location=location)
            self.save_challenge()
        except DuplicateFlagError:
            raise

    def list_flags(self):
        if not self.challenge:
            raise NoChallengeSelectedError
        return "\n".join(str(flag) for flag in self.challenge.get_flags())

    def get_challenge_points(self, username):
        if not self.challenge:
            raise NoChallengeSelectedError
        return self.challenge.get_challenge_points(username)

    def delete_flag(self, flag):
        if not self.challenge:
            raise NoChallengeSelectedError
        try:
            self.challenge.delete_flag(flag)
            self.save_challenge()
        except FlagNotFoundError:
            raise

    def capture_flag(self, username, text):
        if not self.challenge:
            raise NoChallengeSelectedError
        response = self.challenge.validate_flag(username, text)
        if response and response[0] == FLAG_CAPTURED_SUCCESSFULLY:
            self.save_challenge()
        return response

    def create_hint(self, hint, level, cost=0):
        if not self.challenge:
            raise NoChallengeSelectedError
        pass

    def list_hints(self):
        if not self.challenge:
            raise NoChallengeSelectedError
        pass

    def delete_hint(self, hint):
        if not self.challenge:
            raise NoChallengeSelectedError
        pass

    def reveal_hint(self):
        if not self.challenge:
            return "No hints available at this time"
        return self.challenge.reveal_next_hint()

    def create_objective(self, objective, level):
        if not self.challenge:
            raise NoChallengeSelectedError
        pass

    def list_objectives(self):
        if not self.challenge:
            raise NoChallengeSelectedError
        pass

    def delete_objective(self, objective):
        if not self.challenge:
            raise NoChallengeSelectedError
        pass

    def get_current_objective(self):
        if not self.challenge:
            raise NoChallengeSelectedError
        objective = self.challenge.objective
        if objective:
            return self.challenge.objective
        elif not objective and hasattr(settings, 'DEFAULT_OBJECTIVE'):
            return settings.DEFAULT_OBJECTIVE
        else:
            return "There is no objective set at the moment"

    def set_current_objective(self, objective):
        if not self.challenge:
            raise NoChallengeSelectedError
        self.challenge.objective = objective
        self.save_challenge()
    # endregion challenge

    # region twitchbot
    def get_subscriptions(self):
        if self.profile and self.profile.channel_id:
            cid = self.profile.channel_id
            return [f'channel-bits-events-v2.{cid}',
                    f'channel-points-channel-v1.{cid}',
                    f'channel-subscribe-events-v1.{cid}',
                    f'chat_moderator_actions.{cid}',
                    f'whispers.{cid}']
        logger.error("Missing configuration for PubSub subscriptions")
        return []

    def initialize_twitch(self):
        if self.twitchbot:
            logger.error("Twitch aleady initialized")
        if not self.profile.bot_name:
            self.twitchbot = TwitchBot(self, nick=self.profile.channel_name,
                                       client_id=self.profile.client_id,
                                       irc_token=f'oauth:{self.profile.api_token}',
                                       api_token=self.profile.api_token,
                                       initial_channels=[self.profile.channel_name])
        else:
            self.twitchbot = TwitchBot(self, nick=self.profile.bot_name,
                                       client_id=self.profile.client_id,
                                       irc_token=f'oauth:{self.profile.irc_token}',
                                       api_token=self.profile.api_token,
                                       initial_channels=[self.profile.channel_name])

    def twitchbot_status(self):
        if not self.profile:
            raise NoProfileSelectedError
        status = "not initialized"
        if self.twitchbot:
            status = "initialized"
            if self.twitchbot.connection:
                status += " and connected"
        return f"Twitchbot is {status}"

    def connect_twitch(self):
        if not self.profile:
            raise NoProfileSelectedError
        if self.twitchbot and not self.twitchbot.connection:
            self.twitchbot.connect()

    def disconnect_twitch(self):
        if not self.profile:
            raise NoProfileSelectedError
        if self.twitchbot and self.twitchbot.connection:
            self.twitchbot.disconnect()
    # endregion twitchbot
