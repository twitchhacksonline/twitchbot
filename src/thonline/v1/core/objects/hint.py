# twitchhacks.online
# "Twitch Hacks Online"
# 2020 - Frank Godo


class Hint:
    def __init__(self, hint_text, level, cost):
        self.text = hint_text
        try:
            self.level = int(level)
            self.cost = int(cost)
            self._order = 999
        except ValueError:
            raise
        self.revealed = False

    def __str__(self):
        return f"ID: {self._order}\tCost: {self.cost}\tRevealed: {self.revealed}\tHint: {self.text}"

    def __eq__(self, obj):
        try:
            return self.text.__eq__(obj.text)
        except AttributeError:
            return False

    def order(self):
        return self._order
