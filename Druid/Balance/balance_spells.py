from Util.spells import Spell, DamageOverTime, Buff
from Util.environment import GeneralEnvironment, DamageType, Resource
from enum import IntFlag
from Druid.Balance.balance_talents import *
from Druid.Balance.balance_constants import *
from Druid.Balance.balance_env_2 import BalanceDruidEnvironment
from random import random


class Spells(IntFlag):
        MOONFIRE = 0
        SUNFIRE = 1
        STELLAR_FLARE = 2
        WRATH = 3
        STARFIRE = 4
        STARSURGE = 5
        STARFALL = 6
        FURY_OF_ELUNE = 7
        WILD_MUSHROOM = 8
        INCARN = 9

# Define all spells
class Moonfire(DamageOverTime):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
                name="Moonfire",
                initial_damage=.2,
                duration_damage=0.174,
                duration=22,
                cast_time=0,
                tick_length=2,
                astral_power=2,
                damage_type=DamageType.ARCANE,
                procs_shooting_stars=True)
        
        self.env = env

    def on_cast(self):
        self.remaining_duration = min(self.remaining_duration + self.duration, 1.3 * self.duration)
        self.env.DoTs.append(self)
        return

    def on_damage(self):
        self.env.calculate_damage(self)

        if self.env.talent_loadout[Talents.shooting_stars]:
            if random() < SHOOTING_STAR_PROC_CHANCE:
                self.env._shooting_star.on_cast()

        if self.env.talent_loadout[Talents.denizen_of_the_dream]:
            if random() < DENIZENS_PROC_CHANCE:
                self.env._denizen_of_the_dream.on_gain()

        return

class Sunfire(DamageOverTime):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(name="Sunfire", 
                 initial_damage=.2,
                 duration_damage=0.174,
                 duration=18,
                 cast_time=0,
                 tick_length=2,
                 astral_power=2,
                 damage_type=DamageType.NATURE,
                 procs_shooting_stars=True)
        
        self.env = env

    def on_cast(self):
        self.remaining_duration = min(self.remaining_duration + self.duration, 1.3 * self.duration)
        self.env.DoTs.append(self)
        return

    def on_damage(self):
        self.env.calculate_damage(self)

        if self.env.talent_loadout[Talents.shooting_stars]:
            if random() < SHOOTING_STAR_PROC_CHANCE:
                self.env._shooting_star.on_damage()

        if self.env.talent_loadout[Talents.denizen_of_the_dream]:
            if random() < DENIZENS_PROC_CHANCE:
                self.env._denizen_of_the_dream.on_gain()

        return

class StellarFlare(DamageOverTime):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(name="Stellar Flare",
                 initial_damage=.125,
                 duration_damage=0.0875,
                 duration=24,
                 cast_time=0,
                 tick_length=2,
                 astral_power=8,
                 damage_type=DamageType.ASTRAL)

        self.env = env

    def on_cast(self):
        self.remaining_duration = min(self.remaining_duration + self.duration, 1.3 * self.duration)
        self.env.DoTs.append(self)
        return

    def on_damage(self):
        self.env.calculate_damage(self)

        if self.env.talent_loadout[Talents.shooting_stars]:
            if random() < SHOOTING_STAR_PROC_CHANCE:
                self.env._shooting_star.on_damage()

        return

class Wrath(Spell):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(name="Wrath",
                 initial_damage=0.5775,
                 cast_time=1.5,
                 astral_power=6,
                 damage_type=DamageType.NATURE) 
        
        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class Starfire(Spell):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
            name="Starfire",
            initial_damage=0.65025,
            cast_time=2.25,
            astral_power=8,
            damage_type=DamageType.ARCANE) 
        
        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class Starsurge(Spell):        
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
            name="Starsurge",
            initial_damage=1.14367,
            cast_time=0,
            astral_power=-40,
            damage_type=DamageType.ASTRAL) 
        
        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class Starfall(Spell):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__()

        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class FuryOfElune(DamageOverTime):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
            name="Fury Of Elune",
            initial_damage=0,
            duration_damage=0.165,
            duration=8,
            cast_time=0,
            tick_length=0.5,
            astral_power=0,
            ap_over_time=40.0 / 16.0,
            damage_type=DamageType.ASTRAL,
            cooldown=60) 
        
        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class WildMushroom():
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__()

        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class FullMoon(Spell):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
            name="Full Moon",
            initial_damage=4.68,
            cast_time=3,
            astral_power=40,
            damage_type=DamageType.ARCANE)
        
        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class ShootingStar(Spell):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
            name="Shooting Star",
            initial_damage=0.18,
            cast_time=0,
            astral_power=2,
            damage_type=DamageType.ASTRAL)
        
        self.env = env

    def on_damage(self):
        self.env.calculate_damage(self)
        
        if self.env.talent_loadout[Talents.orbit_breaker]:
            self.env.orbit_breaker_count += 1

            if self.env.orbit_breaker_count == 30:
                self.env.orbit_breaker_count = 0
                self._full_moon.on_cast()
        return
    
    def on_cast(self):
        self.on_damage()
        self.env.astral_power += self.astral_power
        return

class PowerOfGoldrinn(Spell):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
            name="Power of Goldrinn",
            initial_damage=0.450667,
            cast_time=0,
            astral_power=0,
            damage_type=DamageType.ASTRAL)
        
        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class SunderedFirmament(FuryOfElune):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__()
        self.duration_damage *= SUNDERED_FIRMAMENT_EFFECTIVENESS
        self.ap_over_time *= SUNDERED_FIRMAMENT_EFFECTIVENESS
        self.cooldown = 0
        self.name = "Sundered Firmament"

        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class DenizenOfTheDream(DamageOverTime):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
            name="Denizen of the Dream", 
            initial_damage=0,
            duration_damage=0.1573,
            duration=30,
            cast_time=0,
            tick_length=2,
            astral_power=0,
            damage_type=DamageType.ASTRAL)
        
        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return

class AstralSmolder(DamageOverTime):
    def __init__(self, env: BalanceDruidEnvironment):
        super().__init__(
            name="Astral Smolder",
            initial_damage=0,
            duration_damage=0,
            duration=4,
            cast_time=0,
            tick_length=2,
            damage_type=DamageType.ASTRAL)
        
        self.env = env

    def on_damage(self):
        return
    
    def on_cast(self):
        return
