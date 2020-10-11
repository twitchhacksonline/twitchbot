# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo


class Interaction:
    def __init__(self, username, raw_input, action, profile, challenge):
        self.username = username
        self.raw_input = raw_input
        self.action = action
        self.profile_id = profile
        self.challenge_id = challenge

    def __str__(self):
        return self.action
