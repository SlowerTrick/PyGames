class Data:
    def __init__(self, ui):
        self.ui = ui
        self._coins = 0
        self._player_health = 5
        self.ui.create_hearts(self._player_health)

        self.unlocked_level = 0
        self.current_level = 0

    @property
    def coins(self):
        return self._coins

    @coins.setter
    def coins(self, value):
        self._coins = value
        if self.coins >= 100:
            self.coins -= 100
            self.player_health += 1
        self.ui.show_coins(self.coins)

    @property
    def player_health(self):
        return self._player_health

    @player_health.setter
    def player_health(self, value):
        self._player_health = value
        self.ui.create_hearts(value)