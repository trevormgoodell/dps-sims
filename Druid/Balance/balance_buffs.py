from abc import ABC, abstractmethod
from Druid.Balance.balance_constants import *
from Druid.Balance.balance_talents import *
from Druid.Balance.balance_env_2 import BalanceDruidEnvironment
from Util.environment import DamageType



class Buff(ABC):
    def __init__(   
            self,
            env: BalanceDruidEnvironment, 
            cooldown = 0,
            on_cooldown = False,
            cooldown_end_time = -1,
            useable_on_gcd = True,
            useable_while_casting = False,
            active = False, 
            active_end_time = -1, 
            duration = 0, 
            name = ""):

        self.env = env

        # This is a useless field, but needed for get_actions in Balance
        self.astral_power = 0

        # These deal with the actual spell
        self.cooldown = cooldown
        self.on_cooldown = on_cooldown
        self._cooldown_end_time = cooldown_end_time
        self.useable_on_gcd = useable_on_gcd
        self.useable_while_casting = useable_while_casting

        # These deal with the actual buff
        self.active = active
        self._active_end_time = active_end_time
        self.duration = duration
        
        self.name = name
        
        @property
        def active_end_time(self):
            return round(self._active_end_time, 2)

        @active_end_time.setter
        def active_end_time(self, active_end_time):
            self._active_end_time = active_end_time

        @property
        def cooldown_end_time(self):
            return round(self._cooldown_end_time, 2)

        @cooldown_end_time.setter
        def cooldown_end_time(self, cooldown_end_time):
            self._active_end_time = cooldown_end_time

    @abstractmethod
    def on_gain(self):
        return (self.active_end_time, self)
    
    @abstractmethod
    def on_loss(self):
        pass

class NaturesGrace(Buff):
    def on_gain(self):
        if self in self.env.buffs:
            self.active_end_time = self.env.env_timer.current_time + NATURES_GRACE_BUFF_TIME
            return super().on_gain()

        self.env.update_haste_percent(NATURES_GRACE_HASTE_BUFF)
        self.active_end_time = self.env.env_timer.current_time + NATURES_GRACE_BUFF_TIME
        return super().on_gain()
    
    def on_loss(self):
        self.env.update_haste_percent(-NATURES_GRACE_HASTE_BUFF)
        return
    
class Solstice(Buff):
    def on_gain(self):
        if self in self.env.buffs:
            self.active_end_time = self.env.env_timer.current_time + SOLSTICE_BUFF_TIME
            return super().on_gain()

        SHOOTING_STAR_PROC_CHANCE *= 3
        self.active_end_time = self.env.env_timer.current_time + SOLSTICE_BUFF_TIME
        return super().on_gain()
    
    def on_loss(self):
        SHOOTING_STAR_PROC_CHANCE /= 3
        return
    
class UmbralEmbrace(Buff):
    def on_gain(self):
        if self in self.env.buffs:
            self.active_end_time = self.env.env_timer.current_time + UMBRAL_EMBRACE_BUFF_TIME
            return super().on_gain()

        self.env.wrath.initial_damage *= 1 + (UMBRAL_EMBRACE_DAMAGE_BUFF * self.env.talent_loadout[Talents.umbral_embrace])
        self.env.wrath.damage_type = DamageType.ASTRAL

        self.env.starfire.initial_damage *= 1 + (UMBRAL_EMBRACE_DAMAGE_BUFF * self.env.talent_loadout[Talents.umbral_embrace])
        self.env.starfire.damage_type = DamageType.ASTRAL

        self.active_end_time = self.env.env_timer.current_time + UMBRAL_EMBRACE_BUFF_TIME

        return super().on_gain()
    
    def on_loss(self):
        self.env.wrath.initial_damage /= 1 + (UMBRAL_EMBRACE_DAMAGE_BUFF * self.env.talent_loadout[Talents.umbral_embrace])
        self.env.wrath.damage_type = DamageType.NATURE

        self.env.starfire.initial_damage /= 1 + (UMBRAL_EMBRACE_DAMAGE_BUFF * self.env.talent_loadout[Talents.umbral_embrace])
        self.env.starfire.damage_type = DamageType.ARCANE
        return
    
class StarweaversWeft(Buff):
    def on_gain(self):
        if self in self.env.buffs:
            self.active_end_time = self.env.env_timer.current_time + STARWEAVERS_BUFF_TIME
            return super().on_gain()
        
        self.env.starsurge.astral_power = 0
        self.active_end_time = self.env.env_timer.current_time + STARWEAVERS_BUFF_TIME
        return super().on_gain()
    
    def on_loss(self):
        self.env.starsurge.astral_power = self.env.starsurge._base_astral_power
        return 
    
class StarweaversWarp(Buff):
    def on_gain(self):
        if self in self.env.buffs:
            self.active_end_time = self.env.env_timer.current_time + STARWEAVERS_BUFF_TIME
            return super().on_gain()
        
        self.env.starfall.astral_power = 0
        self.active_end_time = self.env.env_timer.current_time + STARWEAVERS_BUFF_TIME
        return super().on_gain()
    
    def on_loss(self):
        self.env.starfall.astral_power = self.env.starfall._base_astral_power
        return 
    
class CelestialAlignment(Buff):
    def on_gain(self, duration=None):
        if self in self.env.buffs:
            curr_end_time = 0
            for ind in range(len(self.env.buffs)):
                if self == self.env.buffs[ind]:
                    curr_end_time = self.env.buffs[ind][0]
                    del self.env.buffs[ind]
                    break

            if duration:
                self.active_end_time = curr_end_time + duration
            else:
                self.active_end_time = curr_end_time + CELESTIAL_ALIGNMENT_BUFF_TIME

            return super().on_gain()
        
        self.env.update_haste_percent(CELESTIAL_ALIGNMENT_HASTE_BUFF)

        if duration:
            self.active_end_time = self.env.env_timer.current_time + duration
        else:
            self.active_end_time = self.env.env_timer.current_time + CELESTIAL_ALIGNMENT_BUFF_TIME

        return super().on_gain()
    
    def on_loss(self):
        self.env.update_haste_percent(-CELESTIAL_ALIGNMENT_HASTE_BUFF)
        return 
    
class Incarnation(Buff):
    def on_gain(self, duration=None):
        if self in self.env.buffs:
            curr_end_time = 0
            for ind in range(len(self.env.buffs)):
                if self == self.env.buffs[ind]:
                    curr_end_time = self.env.buffs[ind][0]
                    del self.env.buffs[ind]
                    break

            if duration:
                self.active_end_time = curr_end_time + duration
            else:
                self.active_end_time = curr_end_time + INCARNATION_BUFF_TIME
        
            return super().on_gain()
        
        if self.env.talent_loadout[Talents.elunes_guidance]:
            self.env.starsurge.astral_power -= ELUNES_GUIDANCE_STARSURGE
            self.env.starfall.astral_power -= ELUNES_GUIDANCE_STARFALL
        
        self.env.update_haste_percent(CELESTIAL_ALIGNMENT_HASTE_BUFF)
        self.env.critical_strike_percent += INCARNATION_CRIT_BUFF

        if duration:
            self.active_end_time = self.env.env_timer.current_time + duration
        else:
            self.active_end_time = self.env.env_timer.current_time + INCARNATION_BUFF_TIME

        return super().on_gain()
    
    def on_loss(self):
        self.env.update_haste_percent(-CELESTIAL_ALIGNMENT_HASTE_BUFF)
        self.env.critical_strike_percent -= INCARNATION_CRIT_BUFF
        return 
    
class RattleTheStars(Buff):
    def __init__(self, env: BalanceDruidEnvironment, cooldown=0, on_cooldown=False, cooldown_end_time=-1, useable_on_gcd=True, useable_while_casting=False, active=False, active_end_time=-1, duration=0, name=""):
        super().__init__(env, cooldown, on_cooldown, cooldown_end_time, useable_on_gcd, useable_while_casting, active, active_end_time, duration, name)
        self.stacks = 0

    def on_gain(self):
        self.stacks = min(self.stacks + 1, MAX_RATTLE_THE_STARS)

        self.env.starsurge.astral_power = self.env.starsurge._base_astral_power * (1 - RTS_AP_REDUC * self.stacks)
        self.env.starsurge.initial_damage = self.env.starsurge._base_damage * (1 + RTS_DAMAGE_BUFF * self.stacks)
            
        self.env.starfall.astral_power = self.env.starfall._base_astral_power * (1 - RTS_AP_REDUC * self.stacks)
        self.env.starfall.initial_damage = self.env.starfall._base_damage * (1 + RTS_DAMAGE_BUFF * self.stacks)
        
        self.active_end_time = self.active_end_time = self.env.env_timer.current_time + RATTLE_THE_STARS_BUFF_TIME

        return super().on_gain()
    
    def on_loss(self):
        self.stacks = 0

        self.env.starsurge.astral_power = self.env.starsurge._base_astral_power
        self.env.starsurge.initial_damage = self.env.starsurge._base_damage
            
        self.env.starfall.astral_power = self.env.starfall._base_astral_power
        self.env.starfall.initial_damage = self.env.starfall._base_damage
        return