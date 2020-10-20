# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo

import json
from datetime import datetime, timedelta
import logging
import requests

logger = logging.getLogger(__name__)
SCOPES = {
    'irc': ['channel:moderate', 'channel_editor', 'chat:edit', 'chat:read', 'whispers:edit', 'whispers:read'],
    'api': ['bits:read', 'channel:moderate', 'channel:read:redemptions', 'channel:read:subscriptions',
            'channel_subscriptions', 'chat:edit', 'chat:read', 'clips:edit', 'moderation:read', 'user:edit:broadcast',
            'whispers:edit', 'whispers:read']
}


class Token:
    def __init__(self, type):
        self.type = type
        self.token = None
        self.scopes = SCOPES.get(type, [])
        self.user_id = None
        self.login = None
        self.expiry = datetime.now()

    def __str__(self):
        return self.token

    def expired(self):
        expired = self.expiry <= datetime.now()
        if expired:
            logger.warn("Token for %s has expired", self.type)
        else:
            if (self.expiry - timedelta(days=7)) < datetime.now():
                warning = f"Token for {self.type} will expire in less than a week"
                print(warning)
                logger.warn(warning)
        return expired

    def validate(self):
        try:
            response = json.loads(requests.get('https://id.twitch.tv/oauth2/validate',
                                  headers={'Authorization': 'Bearer ' + self.token}).text)
            logger.debug(response)
            assert response.get('scopes', []) == self.scopes
            delta = timedelta(seconds=response.get('expires_in', 0))
            assert delta.total_seconds() > 0
            self.expiry = datetime.now() + delta
            if not self.login:
                self.login = response.get('login')
            if not self.user_id:
                self.user_id = int(response.get('user_id'))
            return True
        except (TypeError, AssertionError) as e:
            logger.exception(e)
            return False

    def generate(self):
        # Start a webserver, and print the url for user to click on
        # Catch the response and parse out the token
        pass
