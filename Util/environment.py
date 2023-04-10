import numpy as np
import Util.util as util
from enum import auto, IntFlag
from Util.simulation_timer import Timer

class GeneralEnvironment():
    def __init__(self, max_time=300, time_step=0.01, haste=0, critical_strike=0, versatility=0, mastery=0, main_stat=0):
        """
        The base environment that simulates the 'env' in OpenAI Gym.
        This class is intended to be used as an interface

        Attributes:
        max_time = Maximum fight length in seconds
        current_time = Time progressed in the simulation in seconds
        time_step = How often the time updates in seconds
        total_damage = How much damage has been done total
        """
        # Actions
        self.actions = {}
        self.state = np.array([])
        
        self._current_time = 0
        self.max_time = max_time
        self.time_step = time_step
        self.total_damage = 0

        self.env_timer = Timer(max_time, time_step, self)

        # Game Mechanics
        self.spell_power = 0
        self.flat_damage_modifier = 1

        # Every class uses resources so this is the default entry for it.
        # Make sure to override in child class
        self.resource = Resource(0, 100, 0, 1, 0)

        # Character Stats by value (not percentage)
        self._haste = 0
        self._critical_strike = 0
        self._versatility = 0
        self._mastery = 0
        self._main_stat = 0

        # Character Stats by percentage
        self.haste_percent = 0
        self.critical_strike_percent = 0
        self.versatility_percent = 0
        self.mastery_percent = 0

        # Base percent values, should be numbers between 0-100 NOT DECIMAL FORM
        # base_crit_percent and base_mastery_percent are intentionally left blank
        # Must be initialized in child class
        self._base_haste_percent = 0
        self._base_crit_percent
        self._base_verse_percent = 0
        self._base_mastery_percent

        # This is handled by the setters below, put at the bottom to give classes the time to modify any base arguments as needed
        self.haste = haste
        self.critical_strike = critical_strike
        self.versatility = versatility
        self.mastery = mastery
        self.main_stat = main_stat
        
    @property
    def haste(self):
        return self._haste

    @haste.setter
    def haste(self, haste):
        self._haste = haste
        self.haste_percent = util.DiminishSecondaryStat("Haste", haste) / 100
        self.env_timer.global_cooldown = round(self.env_timer._base_global_cooldown / (self.haste_percent + 1), 2)


    @property
    def critical_strike(self):
        return self._critical_strike

    @critical_strike.setter
    def critical_strike(self, critical_strike):
        self._critical_strike = critical_strike
        self.critical_strike_percent = util.DiminishSecondaryStat("Critical Strike", critical_strike, point_conversion = 1, base_val = self._base_crit_percent) / 100
    
    @property
    def versatility(self):
        return self._versatility

    @versatility.setter
    def versatility(self, versatility):
        self._versatility = versatility
        self.versatility_percent = util.DiminishSecondaryStat("Versatility", versatility, point_conversion = 1, base_val = self._base_verse_percent) / 100

    @property
    def mastery(self):
        return self._mastery

    @mastery.setter
    def mastery(self, mastery):
        self._mastery = mastery
        self.mastery_percent = util.DiminishSecondaryStat("Mastery", mastery, point_conversion = self._point_conversion, base_val = self._base_mastery_percent) / 100

    @property
    def main_stat(self):
        return self._main_stat

    @main_stat.setter
    def main_stat(self, main_stat):
        self._main_stat = main_stat
        self.spell_power = 0.92 * self.main_stat

    
    def update_haste_percent(self, gained_haste):
        haste_mod = np.abs(gained_haste)

        if gained_haste > 0:
            self.haste *= (1+haste_mod)
            self.haste_percent += haste_mod

        if gained_haste < 0:
            self.haste_percent -= haste_mod
            self.haste /= (1+haste_mod)    

    def step(self, action):
        # Update the time
        self.current_time += self.time_step

        if action == 'NOOP':
            pass

class DamageType(IntFlag):
    PHYSICAL = auto()
    ARCANE = auto()
    FIRE = auto()
    FROST = auto()
    NATURE = auto()
    SHADOW = auto()
    HOLY = auto()
    ASTRAL = ARCANE | NATURE
    CHAOS = ARCANE | FIRE | FROST | NATURE | SHADOW
    COSMIC = ARCANE | HOLY | NATURE | SHADOW
    DIVINE = ARCANE | HOLY
    ELEMENTAL = FIRE | FROST | NATURE
    FLAMESTRIKE = FIRE | PHYSICAL
    FIRESTORM = FIRE | NATURE
    FROSTFIRE = FROST | FIRE
    FROSTSTORM = FROST | NATURE
    PLAGUE = NATURE | SHADOW
    RADIANT = FIRE | HOLY
    SHADOWFLAME = FIRE | SHADOW
    SHADOWFROST = SHADOW | FROST
    SHADOWSTRIKE = SHADOW | PHYSICAL
    SPELLFROST = ARCANE | FROST
    SPELLSHADOW = ARCANE | SHADOW
    TWILIGHT = HOLY | SHADOW
    VOLCANIC = FIRE | NATURE

    def __eq__(self, data_type):
        return (self & data_type) > 0

class Resource():
    def __init__(self, low, high, gain, every, default = 0):
        """
        Class to manage resources for all classes

        inputs:
        low = lowest possible value for your resource
        high = highest possible value for your resource
        gain = default resource gained in combat (e.g. in combat mana regen, nature's balance)
        every = how often the timer for 'gain' ticks
        default = starting value of your resource
        """
        self.low = low
        self.high = high
        self.gain = gain
        self.every = every
        self._current = default
        pass

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, current):
        self._current = min(current, self.high)

    def combat_gain(self, timer):
        if round(timer, 2) % self.every == 0:
            self.current += self.gain

    def __add__(self, gained):
        self.current += gained
        return self

    def __eq__(self, other):
        return self.current == other

    def __lt__(self, other):
        return self.current < other

    def __le__(self, other):
        return self.current <= other

    def __gt__(self, other):
        return self.current > other

    def __ge__(self, other):
        return self.current >= other

    def __ne__(self, other):
        return self.current != other
