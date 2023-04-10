class Spell():
    def __init__(self,
        name,
        initial_damage, 
        cast_time, 
        astral_power, 
        damage_type, 
        cooldown = 0, 
        sets_gcd = True, 
        useable_while_casting = False, 
        useable_on_gcd = False, 
        on_cooldown = False,
        cooldown_end_time = -1):
        """
        Represents classes, which will make up all possible actions.

        Attributes:
        name = name of the spell, mostly used for seeing what the algorithm does
        initial_damage = how much damage the spell does or it's initial hit if a dot
        duration_damage = how much damage it does over a duration
        cast_time = how long it takes to cast, 0 means it's instant
        tick_length = how often the duration damage ticks
        ap = how much ap is affected by this spell, >0 means gain, <0 means loss, =0 means no change
        damage_type = school of damage that is modified by certain buffs

        Damages are represented as % spell power
        Times are base durations, haste will be applied when taking the step
        """

        self.name = name
        self.initial_damage = initial_damage
        self._base_damage = initial_damage
        
        self.cast_time = cast_time
        self.astral_power = astral_power
        self._base_astral_power = astral_power
        self.damage_type = damage_type
        self.cooldown = cooldown
        self.sets_gcd = sets_gcd
        self.useable_while_casting = useable_while_casting
        self.useable_on_gcd = useable_on_gcd
        self.on_cooldown = on_cooldown
        self.cooldown_end_time = cooldown_end_time
        self._base_cast_time = cast_time

class DamageOverTime(Spell):
    def __init__(self, 
        name, 
        initial_damage, 
        duration_damage, 
        duration, 
        cast_time, 
        tick_length, 
        astral_power, 
        damage_type, 
        useable_while_casting=False, 
        useable_on_gcd=False, 
        cooldown = 0, 
        sets_gcd = True, 
        last_tick = -1, 
        remaining_duration = 0, 
        next_tick = -1, 
        next_ap_tick = -1, 
        end_time = -1, 
        ap_over_time = 0, 
        procs_shooting_stars = False, 
        on_cooldown = False,
        cooldown_end_time = -1):

        super().__init__(
            name=name, 
            initial_damage=initial_damage, 
            cast_time=cast_time, 
            astral_power=astral_power, 
            damage_type=damage_type, 
            cooldown=cooldown, 
            sets_gcd=sets_gcd, 
            useable_while_casting=useable_while_casting, 
            useable_on_gcd=useable_on_gcd, 
            on_cooldown=on_cooldown,
            cooldown_end_time=cooldown_end_time)

        self.duration = duration
        self.duration_damage = duration_damage
        self.tick_length = tick_length
        self.last_tick = last_tick
        self.remaining_duration = remaining_duration
        self.next_tick = next_tick
        self.next_ap_tick = next_ap_tick
        self.end_time = end_time
        self.ap_over_time = ap_over_time
        self.procs_shooting_stars = procs_shooting_stars


class Buff():
    def __init__(   self, 
                    cooldown = 0,
                    on_cooldown = False,
                    cooldown_end_time = -1,
                    useable_on_gcd = True,
                    useable_while_casting = False,
                    active = False, 
                    active_end_time = -1, 
                    duration = 0, 
                    name = "") -> None:

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