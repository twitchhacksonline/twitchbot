# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo


class Objective:
    def __init__(self, objective_text, level):
        self.text = objective_text
        try:
            self.level = int(level)
        except ValueError:
            raise

    def __str__(self):
        return f"Level: {self.level}\tObjective: {self.text}"

    def get_level(self):
        return self.level
