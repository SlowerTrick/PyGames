class Data:
    def __init__(self, ui):
        self.ui = ui
        self._coins = 0
        self._player_health = 5
        self._max_player_heath = 5
        self._health_regen = False
        self._string_bar = 0
        self._max_string_bar = 6
        self._actual_weapon = 0
        self._max_actual_weapon = 2
        self._max_weapon = 2
        self.ui.create_ui_bar(self._health_regen)
        self.ui.create_hearts(self._player_health, self._max_player_heath)
        self.ui.create_string_bar(self._string_bar)
        self.ui.create_weapons_frame(0)

        # Habilidades desbloqueaveis
        self.unlocked_wall_jump = False
        self.unlocked_dash = False
        self.unlocked_throw_attack = False
        self.unlocked_weapons = False

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
        if self._player_health >= self._max_player_heath:
            self._player_health = self._max_player_heath
        self.ui.create_hearts(value, self._max_player_heath)
    
    @property
    def health_regen(self):
        return self._health_regen

    @health_regen.setter
    def health_regen(self, value):
        self._health_regen = value
        self.ui.create_ui_bar(self._health_regen)
        self.player_health = self._player_health
    
    @property
    def string_bar(self):
        return self._string_bar

    @string_bar.setter
    def string_bar(self, value):
        self._string_bar = value
        if self._string_bar >= self._max_string_bar:
            self.health_regen = True
            self._string_bar = self._max_string_bar
        if self._string_bar < 0:
            self._string_bar = 0
        self.ui.create_string_bar(self._string_bar)
    
    @property
    def actual_weapon(self):
        return self._actual_weapon

    @actual_weapon.setter
    def actual_weapon(self, value):
        self._actual_weapon = value
        if self._actual_weapon > self._max_weapon:
            self._actual_weapon = 1
        self.ui.create_weapons_frame(self._actual_weapon)