from doctest import master
import Util.util as util
from Util.environment import GeneralEnvironment, DamageType, Resource
from Util.spells import Spell, DamageOverTime
import numpy as np
from enum import IntFlag, Enum
from Druid.Balance.balance_spells import *

class Spells(IntFlag):
        MOONFIRE = 0
        SUNFIRE = 1
        STELLAR_FLARE = 2
        WRATH = 3
        STARFIRE = 4
        STARSURGE = 5
        FURY_OF_ELUNE = 6
        INCARN = 7
        RAVENOUS_FRENZY = 8
        ORB = 9


class BalanceDruidEnvironment(GeneralEnvironment):
    def __init__(self, haste, critical_strike, versatility, mastery, main_stat):
        self._base_crit_percent = 8.0
        self._base_mastery_percent = 8.0

        super().__init__(haste=haste,
                         critical_strike=critical_strike,
                         versatility=versatility,
                         mastery=mastery,
                         main_stat=main_stat)

        # 10% buff for being in Moonkin form
        self.flat_damage_modifier += .1 

        # Store base values for reset
        self._base_haste = haste
        self._base_critical_strike = critical_strike
        self._base_mastery = mastery
        self._base_versatility = versatility
        self._base_main_stat = main_stat

        # Add spells to action space
        self.actions[Spells.MOONFIRE] = Moonfire()
        self.actions[Spells.SUNFIRE] = Sunfire()
        self.actions[Spells.STELLAR_FLARE] = StellarFlare()
        self.actions[Spells.WRATH] = Wrath()
        self.actions[Spells.STARFIRE] = Starfire()
        self.actions[Spells.STARSURGE] = Starsurge()
        self.actions[Spells.FURY_OF_ELUNE] = FuryOfElune()
        self.actions[Spells.INCARN] = Incarn()

        self.actions[Spells.STELLAR_FLARE].cast_time = self.actions[Spells.STELLAR_FLARE]._base_cast_time / (1 + self.haste_percent)
        self.actions[Spells.WRATH].cast_time = self.actions[Spells.WRATH]._base_cast_time / (1 + self.haste_percent)
        self.actions[Spells.STARFIRE].cast_time = self.actions[Spells.STARFIRE]._base_cast_time / (1 + self.haste_percent)

        tier_reduction = 0.15
        self.ss_base_cost = self.actions[Spells.STARSURGE].astral_power
        self.ss_reduced_cost = self.ss_base_cost * (1 - tier_reduction)

        self._shooting_stars = ShootingStar()
        self.shooting_star_proc = 0.15

        self._celestial_pillar = FuryOfElune()
        self._celestial_pillar.duration_damage *= 0.2
        self._celestial_pillar.name = "Celestial Pillar"

        # Results
        self.results = {
            self.actions[Spells.MOONFIRE].name: [0, 0],
            self.actions[Spells.MOONFIRE].name + " (DoT)": [0, 0],
            self.actions[Spells.SUNFIRE].name: [0, 0],
            self.actions[Spells.SUNFIRE].name + " (DoT)": [0, 0],
            self.actions[Spells.STELLAR_FLARE].name: [0, 0],
            self.actions[Spells.STELLAR_FLARE].name + " (DoT)": [0, 0],
            self.actions[Spells.WRATH].name: [0, 0],
            self.actions[Spells.STARFIRE].name: [0, 0],
            self.actions[Spells.STARSURGE].name: [0, 0],
            self.actions[Spells.FURY_OF_ELUNE].name: [0, 0],
            self.actions[Spells.FURY_OF_ELUNE].name + " (DoT)": [0, 0],
            self._shooting_stars.name: [0, 0],
            self._celestial_pillar.name + " (DoT)": [0, 0]
        }
        self.ap_chart = []
        self.solar_eclipse_chart = []
        self.lunar_eclipse_chart = []
        self.rf_chart = []
        self.pulsar_chart = []
        self.incarn_active = []
        
        # Assuming Nature's Balance is selected
        self.astral_power = Resource(0, 100, 1, 2, 51)

        self._starfire_until_solar_eclipse = 2
        self._in_solar_eclipse = False

        self._wrath_until_lunar_eclipse = 2
        self._in_lunar_eclipse = False

        # Buffs
        self._in_incarn = False
        self.incarn_end_time = 0

        self._pulsar_progress = 0

        self.spells_on_cd = []
        self.active_buffs = []

        self.orb_end_time = -1

        self.ravenous_frenzy_end_time = -1
        self.ravenous_frenzy_stacks = 0

        self.ravenous_exhaust = RavenousExhaust()
        self.lunar_eclipse = LunarEclipse()
        self.solar_eclipse = SolarEclipse()

        self.state = self.get_state()

    @property
    def wrath_until_lunar_eclipse(self):
        return self._wrath_until_lunar_eclipse

    @wrath_until_lunar_eclipse.setter
    def wrath_until_lunar_eclipse(self, wrath_until_lunar_eclipse):
        self._wrath_until_lunar_eclipse = wrath_until_lunar_eclipse

        if self._wrath_until_lunar_eclipse == 0:
            # Make it so that you cannot enter an eclipse while in another eclipse
            self.wrath_until_lunar_eclipse = -1
            self.starfire_until_solar_eclipse = -1

            # Turn on Lunar Eclipse
            self.in_lunar_eclipse = True
            self.lunar_eclipse.active = True
            self.lunar_eclipse.active_end_time = self.env_timer.current_time + self.lunar_eclipse.duration
            self.active_buffs.append(self.lunar_eclipse)

            # Keep track of lunar eclipse timer
            self.lunar_eclipse_start_time = self.env_timer.current_time
            self.lunar_eclipse_end_time = self.lunar_eclipse.active_end_time

            # Add lunar eclipse benefits to starfire
            # Crit strike is managed in calc_damage()
            self.actions[Spells.STARFIRE].cast_time /= (1.15)
    
    @property
    def starfire_until_solar_eclipse(self):
        return self._starfire_until_solar_eclipse

    @starfire_until_solar_eclipse.setter
    def starfire_until_solar_eclipse(self, starfire_until_solar_eclipse):
        self._starfire_until_solar_eclipse = starfire_until_solar_eclipse

        if self._starfire_until_solar_eclipse == 0:
            self.wrath_until_lunar_eclipse = -1
            self.starfire_until_solar_eclipse = -1

            # Turn on Solar Eclipse
            self.in_solar_eclipse = True
            # self.solar_eclipse.active = True
            self.solar_eclipse.active_end_time = self.env_timer.current_time + self.solar_eclipse.duration
            self.active_buffs.append(self.solar_eclipse)

            # Keep track of solar eclipse timer
            self.solar_eclipse_start_time = self.env_timer.current_time
            self.solar_eclipse_end_time = self.solar_eclipse.active_end_time

            # Add solar eclipse benefits to wrath
            self.actions[Spells.WRATH].cast_time /= (1.15)
            self.actions[Spells.WRATH].initial_damage *= 1.2

    @property
    def in_solar_eclipse(self):
        return self.solar_eclipse.active

    @in_solar_eclipse.setter
    def in_solar_eclipse(self, in_solar_eclipse):
        # Leaving a solar eclipse
        if self.in_solar_eclipse == True and in_solar_eclipse == False:
            self.starfire_until_solar_eclipse = -1
            self.wrath_until_lunar_eclipse = 2

        self._in_solar_eclipse = in_solar_eclipse
        self.solar_eclipse.active = in_solar_eclipse

    @property
    def in_lunar_eclipse(self):
        return self.lunar_eclipse.active

    @in_lunar_eclipse.setter
    def in_lunar_eclipse(self, in_lunar_eclipse):
        # Leaving a lunar eclipse
        if self.in_lunar_eclipse == True and in_lunar_eclipse == False: 
            self.wrath_until_lunar_eclipse = -1
            self.starfire_until_solar_eclipse = 2

        # Entering lunar eclipse procs celestial pillar for 8 seconds
        if in_lunar_eclipse == True:
            active = self._celestial_pillar.remaining_duration > 0
            self._celestial_pillar.remaining_duration += 8
            self._celestial_pillar.end_time = self.env_timer.current_time + 8

            if not active:
                self._celestial_pillar.next_tick = self._celestial_pillar.tick_length / (1 + self.haste_percent) + self.env_timer.current_time
                self._celestial_pillar.next_ap_tick = self._celestial_pillar.tick_length + self.env_timer.current_time

        self.lunar_eclipse.active = in_lunar_eclipse

    @property
    def in_incarn(self):
        return self._in_incarn

    @in_incarn.setter
    def in_incarn(self, in_incarn):
        state, duration = in_incarn
        prev_in_incarn = self.actions[Spells.INCARN].active
        # Leaving incarn
        if state == False: 
            self.actions[Spells.INCARN].active = False

            self.wrath_until_lunar_eclipse = 2
            self.starfire_until_solar_eclipse = 2

            self.solar_eclipse.active_end_time = -1
            self.lunar_eclipse.active_end_time = -1

            self.lunar_eclipse.active = False
            self.solar_eclipse.active = False

            # Update stats
            self.update_haste_percent(-0.1)
            self.critical_strike_percent -= 0.1

        if state == True:
            self.actions[Spells.INCARN].active = True

            # Briefly turn off lunar and solar eclipse to reset them
            self.lunar_eclipse.active = False
            self.solar_eclipse.active = False

            self.wrath_until_lunar_eclipse = -1
            self.starfire_until_solar_eclipse = -1

            # Update stats
            if not prev_in_incarn:
                self.update_haste_percent(0.1)
                self.critical_strike_percent += 0.1

            # Proc celestial pillar
            active = self._celestial_pillar.remaining_duration > 0
            self._celestial_pillar.remaining_duration += 8
            self._celestial_pillar.end_time = self.env_timer.current_time + self._celestial_pillar.remaining_duration
            if not active:
                self._celestial_pillar.next_tick = self._celestial_pillar.tick_length / (1 + self.haste_percent) + self.env_timer.current_time
                self._celestial_pillar.next_ap_tick = self._celestial_pillar.tick_length + self.env_timer.current_time


            if duration == 12:
                mins = int(self.env_timer.current_time // 60)
                secs = round(self.env_timer.current_time - (mins * 60), 2)
                output = "{mins:d}:{secs:.2f}"
                # print(output.format(mins=mins, secs=secs))
            # If incarn is already active, add to the duration, otherwise set the end time
            if self.incarn_end_time > self.env_timer.current_time:
                self.incarn_end_time += duration
            else:
                self.incarn_end_time = self.env_timer.current_time + duration

            self.actions[Spells.INCARN].active_end_time = self.incarn_end_time

            # Turn on Solar and Lunar Eclipse
            self._in_solar_eclipse = True
            self._in_lunar_eclipse = True

            # Keep track of solar eclipse timer
            self.solar_eclipse.active_end_time = self.incarn_end_time
            self.lunar_eclipse.active_end_time = self.incarn_end_time
            self.lunar_eclipse.active = True
            self.solar_eclipse.active = True

            temp = []

            for buff in self.active_buffs:
                if buff.name == self.lunar_eclipse.name or buff.name == self.solar_eclipse.name:
                    continue
                else:
                    temp.append(buff)
                
            self.active_buffs = temp

            if not prev_in_incarn:
                self.active_buffs.append(self.actions[Spells.INCARN])

        self._in_incarn = state

    @property
    def pulsar_progress(self):
        return self._pulsar_progress

    @pulsar_progress.setter
    def pulsar_progress(self, ap_spent):
        ap_spent = np.abs(ap_spent)
        self._pulsar_progress += ap_spent

        # Every 300 astral power spent procs incarn for 12 seconds
        if self._pulsar_progress >= 300:
            self.in_incarn = (True, 12)
            self._pulsar_progress %= 300
            
    @property
    def haste(self):
        return self._haste

    @haste.setter
    def haste(self, haste):
        self._haste = haste
        self.haste_percent = util.DiminishSecondaryStat("Haste", haste) / 100
        self.env_timer.global_cooldown = round(self.env_timer._base_global_cooldown / (self.haste_percent + 1), 2)

        for key, value in self.actions.items():
            if isinstance(self.actions[key], Spell):
                self.actions[key].cast_time = self.actions[key]._base_cast_time / (1 + self.haste_percent)

                if key == Spells.WRATH and self.solar_eclipse.active:
                    self.actions[key].cast_time = self.actions[key].cast_time / (1.15)

                if key == Spells.STARFIRE and self.lunar_eclipse.active:
                    self.actions[key].cast_time = self.actions[key].cast_time / (1.15)

    
    def get_modifier(self, damage_type):
        solar_modifier = 1
        lunar_modifier = 1

        if self.in_solar_eclipse and damage_type == DamageType.NATURE:
            solar_modifier += self.mastery_percent

        if self.in_lunar_eclipse > 0 and damage_type == DamageType.ARCANE:
            lunar_modifier += self.mastery_percent

        modifier = solar_modifier * lunar_modifier * (1 + self.versatility_percent) * self.flat_damage_modifier * (1 + 0.02 * self.ravenous_frenzy_stacks)

        return modifier

    def calc_damage(self, damage_type, base_damage):
        if self._current_action == Spells.STARFIRE and self.in_lunar_eclipse:
            critical_hit = np.random.uniform() < (self.critical_strike_percent + .2)
        else:
            critical_hit = np.random.uniform() < self.critical_strike_percent

        modifier = self.get_modifier(damage_type)
        
        damage = base_damage * self.spell_power * modifier

        return damage + (damage * critical_hit)

    def apply_shooting_stars(self):
        shooting_star_hit = np.random.uniform() < self.shooting_star_proc

        if shooting_star_hit:
            damage = self.calc_damage(self._shooting_stars.damage_type, self._shooting_stars.initial_damage)
            self.results[self._shooting_stars.name][0] += damage
            self.results[self._shooting_stars.name][1] += 1
            self.astral_power += self._shooting_stars.astral_power
        else:
            damage = 0

        return damage

    def calc_dot_damage(self, spell):
        shooting_star_dam = 0
        damage = 0

        if self.env_timer.current_time // spell.end_time == 1:
            if spell.procs_shooting_stars:
                shooting_star_dam = self.apply_shooting_stars()

            damage = self.calc_damage(spell.damage_type, spell.duration_damage)
            damage *= (self.env_timer.current_time - spell.last_tick) / (spell.tick_length / (1 + self.haste_percent))
            
            self.astral_power += spell.ap_over_time

            self.results[spell.name + " (DoT)"][0] += damage
            self.results[spell.name + " (DoT)"][1] += 1
            
            spell.remaining_duration = 0

        if self.env_timer.current_time // spell.next_tick == 1:
            if spell.procs_shooting_stars:
                shooting_star_dam = self.apply_shooting_stars()

            spell.next_tick = spell.tick_length / (1 + self.haste_percent) + self.env_timer.current_time
            spell.last_tick = self.env_timer.current_time
            
            damage = self.calc_damage(spell.damage_type, spell.duration_damage)
                        
            self.results[spell.name + " (DoT)"][0] += damage
            self.results[spell.name + " (DoT)"][1] += 1

        if spell.remaining_duration > 0:
            spell.remaining_duration -= self.env_timer.time_step
        
        self.total_damage += (damage + shooting_star_dam)
        
        return

    def update_dots(self):
        if self.actions[Spells.MOONFIRE].remaining_duration > 0:
            self.calc_dot_damage(self.actions[Spells.MOONFIRE])

        if self.actions[Spells.SUNFIRE].remaining_duration > 0:
            self.calc_dot_damage(self.actions[Spells.SUNFIRE])

        if self.actions[Spells.STELLAR_FLARE].remaining_duration > 0:
            self.calc_dot_damage(self.actions[Spells.STELLAR_FLARE])

        if self.actions[Spells.FURY_OF_ELUNE].remaining_duration > 0:
            self.calc_dot_damage(self.actions[Spells.FURY_OF_ELUNE])

        if self._celestial_pillar.remaining_duration > 0:
            self.calc_dot_damage(self._celestial_pillar)
        
    def get_state(self):
        # Buff Uptime
        rem_solar = self.solar_eclipse.active_end_time - self.env_timer.current_time if self.solar_eclipse.active else 0
        rem_lunar = self.lunar_eclipse.active_end_time - self.env_timer.current_time if self.lunar_eclipse.active else 0

        # CD time
        foe_cd = 0 if not self.actions[Spells.FURY_OF_ELUNE].on_cooldown else self.actions[Spells.FURY_OF_ELUNE].cooldown_end_time - self.env_timer.current_time
        rf_cd = 0 if not self.actions[Spells.RAVENOUS_FRENZY].on_cooldown else self.actions[Spells.RAVENOUS_FRENZY].cooldown_end_time - self.env_timer.current_time
        incarn_cd = 0 if not self.actions[Spells.INCARN].on_cooldown else self.actions[Spells.INCARN].cooldown_end_time - self.env_timer.current_time
        orb_cd = 0 if not self.actions[Spells.ORB].on_cooldown else self.actions[Spells.ORB].cooldown_end_time - self.env_timer.current_time

        incarn_active = 1 if self.actions[Spells.INCARN].active else 0 
        rf_active = 1 if self.actions[Spells.RAVENOUS_FRENZY].active else 0 
        orb_active = 1 if self.actions[Spells.ORB].active else 0 

        incarn_rem_dur = self.actions[Spells.INCARN].active_end_time - self.env_timer.current_time if incarn_active else 0
        rf_rem_dur = self.actions[Spells.RAVENOUS_FRENZY].active_end_time - self.env_timer.current_time if rf_active else 0
        orb_rem_dur = self.actions[Spells.ORB].active_end_time - self.env_timer.current_time if orb_active else 0


        state = np.array([
            self.actions[Spells.MOONFIRE].remaining_duration,       # 0
            self.actions[Spells.SUNFIRE].remaining_duration,        # 1
            self.actions[Spells.STELLAR_FLARE].remaining_duration,  # 2
            self.astral_power.current,                              # 3
            self.wrath_until_lunar_eclipse,                         # 4
            self.starfire_until_solar_eclipse,                      # 5
            self.in_solar_eclipse,                                  # 6
            self.in_lunar_eclipse,                                  # 7
            rem_solar,                                              # 8
            rem_lunar,                                              # 9
            foe_cd,                                                 # 10
            rf_cd,                                                  # 11
            incarn_cd,                                              # 12
            orb_cd,                                                 # 13
            incarn_active,                                          # 14
            rf_active,                                              # 15
            orb_active,                                             # 16
            incarn_rem_dur,                                         # 17
            rf_rem_dur,                                             # 18
            orb_rem_dur,                                            # 19
            self.pulsar_progress                                    # 20
        ])

        return state

    def calc_reward(self, prev_state, action, next_state):
        reward = 0

        if action != -1:
            if isinstance(self.actions[action], DamageOverTime):
                if action == Spells.MOONFIRE:
                    if next_state[0] - prev_state[0] == self.actions[Spells.MOONFIRE].duration:
                        reward += 1
                    else:
                        reward += 5 * ((next_state[0] - prev_state[0]) - self.actions[Spells.MOONFIRE].duration)
                if action == Spells.SUNFIRE:
                    if next_state[1] - prev_state[1] == self.actions[Spells.SUNFIRE].duration:
                        reward += 1
                    else:
                        reward += 5 * ((next_state[1] - prev_state[1]) - self.actions[Spells.SUNFIRE].duration)
                if action == Spells.STELLAR_FLARE:
                    if next_state[2] - prev_state[2] == self.actions[Spells.STELLAR_FLARE].duration:
                        reward += 1
                    else:
                        reward += 5 * ((next_state[2] - prev_state[2]) - self.actions[Spells.STELLAR_FLARE].duration)
            
            if isinstance(self.actions[action], Spell):
                if self.actions[action].astral_power > 0:
                    ap_gained = next_state[3] - prev_state[3]
                    # Use greater than or equal to for FoE/Shooting Stars
                    if ap_gained >= self.actions[action].astral_power:
                        reward += ap_gained
                    else:
                        reward += 10 * (ap_gained - self.actions[action].astral_power)
                pass

        # Punished for not being in atleast one eclipse
        if not (next_state[6] or next_state[7]):
            reward -= 300

        if next_state[6] and next_state[7]:
            reward += 100
        
        # Punished for not having dots up
        if next_state[0] == 0:
            reward -= 50
        if next_state[1] == 0:
            reward -= 50
        if next_state[2] == 0:
            reward -= 50

        return reward
        
    def get_actions(self):
        available_actions = {}

        # All these conditions must be met in order for a spell to be valid
        # 1. Not on GCD, if the spell requires it
        # 2. Not casting another spell, if the spell doesn't allow it
        # 3. If it has a cost, you need sufficient resources in order to cast it
        # 4. If it has a cooldown, the spell must not currently be on cd

        for key, action in self.actions.items():
            # Do nothing is always a valid action
            if action == 'NO_OP':
                available_actions[key] = action
                continue

            gcd_valid = False
            casting_valid = False
            resource_valid = False
            cooldown_valid = False
            
            # Checks to see if you can cast while on GCD
            # If not, checks to see if you're on GCD
            if not action.useable_on_gcd:
                if not self.env_timer.on_gcd:
                    gcd_valid = True
            else:
                gcd_valid = True

            # Checks to see if you can use the action while casting
            # If not, checks to see if you're casting
            if not action.useable_while_casting:
                if not self.env_timer.casting:
                    casting_valid = True
            else:
                casting_valid = True

            # Astral power less than 0 means it has a cost (doesn't generate)
            if action.astral_power < 0:
                # If we have more astral power than it costs
                if self.astral_power >= abs(action.astral_power):
                    resource_valid = True
            else:
                resource_valid = True

            if not action.on_cooldown:
                cooldown_valid = True

            # If both conditions are met, then you can use this action
            if gcd_valid and casting_valid and resource_valid and cooldown_valid:
                available_actions[key.value] = action.name

        return available_actions

    def check_buffs(self):
        temp = []

        for buff in list(self.active_buffs):
            term_time = (self.env_timer.current_time // buff.active_end_time) == 1
            if (buff.name == "Lunar Eclipse" or buff.name == "Solar Eclipse") and (buff.active_end_time - self.env_timer.current_time) < 5:

                x = 1
            if buff.name == self.actions[Spells.ORB].name and term_time:
                    self.mastery -= 675
                    self.orb_end_time = -1
                    self.actions[Spells.ORB].active = False
                    self.actions[Spells.ORB].active_end_time = -1

            elif buff.name == self.actions[Spells.INCARN].name and term_time:
                    self.in_incarn = (False, 0)

            elif buff.name == self.actions[Spells.RAVENOUS_FRENZY].name and term_time:
                    self.ravenous_exhaust = RavenousExhaust()
                    self.ravenous_exhaust.active_end_time = self.env_timer.current_time + self.ravenous_exhaust.duration
                    self.ravenous_exhaust.active = True
                    temp.append(self.ravenous_exhaust)

                    self.actions[Spells.RAVENOUS_FRENZY].active = False
                    self.actions[Spells.RAVENOUS_FRENZY].active_end_time = -1

            elif buff.name == self.ravenous_exhaust.name and term_time:
                    self.ravenous_exhaust.active = False
                    self.ravenous_exhaust.active_end_time = -1

                    for _ in range(self.ravenous_frenzy_stacks):
                        self.update_haste_percent(-.01)

                    self.critical_strike_percent -= (0.0176 * self.ravenous_frenzy_stacks)

                    self.ravenous_frenzy_stacks = 0

            elif buff.name == self.solar_eclipse.name and term_time:
                self.in_solar_eclipse = False
                self.solar_eclipse.active = False
                self.actions[Spells.WRATH].initial_damage /= 1.2
                self.actions[Spells.WRATH].cast_time *= (1.15)

            elif buff.name == self.lunar_eclipse.name and term_time:
                self.in_lunar_eclipse = False
                self.lunar_eclipse.active = False
                self.actions[Spells.STARFIRE].cast_time *= (1.15)

            else:
                temp.append(buff)

        self.active_buffs = temp

    def check_cooldowns(self):
        temp = []

        for spell in list(self.spells_on_cd):
            if (self.env_timer.current_time // spell.cooldown_end_time) == 1:
                spell.on_cooldown = False
                spell.cooldown_end_time = -1
            else:
                temp.append(spell)

        self.spells_on_cd = temp

    def reset(self):
        self.__init__(
                    haste=self._base_haste,
                    versatility=self._base_versatility,
                    critical_strike=self._base_critical_strike,
                    mastery=self._base_mastery,
                    main_stat=self._base_main_stat
        )

        return self.get_state()

    def step(self, action):
        """
        step is responsible for updating the total damage during the environment and applying the debuffs.

        Inputs:
        action = a number between 0 and action_space.n that represents what action to perform at this step.
        """
        curr_state = self.get_state()
        damage = 0
        self._current_action = action

        self.ap_chart.append(self.astral_power.current)

        self.check_buffs()

        self.check_cooldowns()
        
        self._current_action = action

        if self.env_timer.current_time % self.astral_power.every == 0:
            self.astral_power += self.astral_power.gain

        if self.env_timer.current_time == self.actions[Spells.FURY_OF_ELUNE].next_ap_tick:
            self.astral_power += self.actions[Spells.FURY_OF_ELUNE].ap_over_time
            self.actions[Spells.FURY_OF_ELUNE].next_ap_tick += self.actions[Spells.FURY_OF_ELUNE].tick_length

        if self.env_timer.current_time == self._celestial_pillar.next_ap_tick:
            self.astral_power += self._celestial_pillar.ap_over_time
            self._celestial_pillar.next_ap_tick += self._celestial_pillar.tick_length

        # Applies on every time step
        self.update_dots()

        if action != -1:
            if self.actions[action].cooldown > 0:
                self.spells_on_cd.append(self.actions[action])
                self.actions[action].on_cooldown = True
                self.actions[action].cooldown_end_time = self.env_timer.current_time + self.actions[action].cooldown
    
            if isinstance(self.actions[action], Spell):
                # Handle duration based things for damage over time effects
                if isinstance(self.actions[action], DamageOverTime):
                    active = self.actions[action].remaining_duration > 0
                    self.actions[action].remaining_duration = min(self.actions[action].remaining_duration + self.actions[action].duration, 1.3 * self.actions[action].duration)
                    if not active:
                        self.actions[action].next_tick = self.actions[action].tick_length / (1 + self.haste_percent) + self.env_timer.current_time
                    self.actions[action].end_time = self.env_timer.current_time + self.actions[action].remaining_duration

                    if self.actions[action].ap_over_time > 0:
                        self.actions[action].next_ap_tick = self.env_timer.current_time + self.actions[action].tick_length

                # Calculate damage of action and add it to total damage
                damage = self.calc_damage(self.actions[action].damage_type, self.actions[action].initial_damage)
                self.total_damage += damage

                # Keep track of how much damage each action does and how often it's used for metrics
                self.results[self.actions[action].name][0] += damage
                self.results[self.actions[action].name][1] += 1

                if self.lunar_eclipse.active or self.solar_eclipse.active:
                    self.actions[Spells.STARSURGE].astral_power = self.ss_reduced_cost
                else:
                    self.actions[Spells.STARSURGE].astral_power = self.ss_base_cost

                # Increase astral power as necessary
                self.astral_power += self.actions[action].astral_power

                # More complicated because pulsar gains full AP when spending, but starsurge is discounted
                if action == Spells.STARSURGE:
                    self.pulsar_progress = 30

                # if action == Spells.STARFALL:
                    # self.pulsar_progress += 50

                # Set the GCD
                self.env_timer.on_gcd = self.actions[action].sets_gcd

                # Set the Cast Time
                self.env_timer.casting = self.actions[action].cast_time

                if self.actions[Spells.RAVENOUS_FRENZY].active:
                    self.ravenous_frenzy_stacks += 1
                    self.update_haste_percent(0.01)
                    self.critical_strike_percent += 0.0176

        # Keep track of going into Lunar Eclipse
        if action == Spells.WRATH and self.wrath_until_lunar_eclipse > 0:
            self.wrath_until_lunar_eclipse -= 1

        # Keep track of going into Solar Eclipse
        if action == Spells.STARFIRE and self.starfire_until_solar_eclipse > 0:
            self.starfire_until_solar_eclipse -= 1

        if action == -1:
            pass

        elif action == Spells.INCARN:
            self.in_incarn = (True, self.actions[Spells.INCARN].duration)

        elif action == Spells.ORB:
            self.env_timer.casting = 2
            self.mastery += 675
            self.orb_end_time = self.env_timer.current_time + self.actions[Spells.ORB].duration
            self.actions[Spells.ORB].active_end_time = self.env_timer.current_time + self.actions[Spells.ORB].duration
            self.actions[Spells.ORB].cooldown_end_time = self.env_timer.current_time + self.actions[Spells.ORB].cooldown
            self.actions[Spells.ORB].on_cooldown = True
            self.actions[Spells.ORB].active = True
            self.env_timer.on_gcd = True
            self.active_buffs.append(self.actions[Spells.ORB])
            self.spells_on_cd.append(self.actions[Spells.ORB])
            pass

        elif action == Spells.RAVENOUS_FRENZY:
            self.actions[Spells.RAVENOUS_FRENZY].active_end_time = self.env_timer.current_time + self.actions[Spells.RAVENOUS_FRENZY].duration
            self.actions[Spells.RAVENOUS_FRENZY].cooldown_end_time = self.env_timer.current_time + self.actions[Spells.RAVENOUS_FRENZY].cooldown
            self.actions[Spells.RAVENOUS_FRENZY].on_cooldown = True
            self.actions[Spells.RAVENOUS_FRENZY].active = True
            self.env_timer.on_gcd = True
            self.active_buffs.append(self.actions[Spells.RAVENOUS_FRENZY])
            self.spells_on_cd.append(self.actions[Spells.RAVENOUS_FRENZY])
            pass

        else:
            pass

        self.env_timer.current_time += self.time_step
        next_state = self.get_state()

        self.rf_chart.append(self.ravenous_frenzy_stacks)
        self.lunar_eclipse_chart.append(self.actions[Spells.WRATH].cast_time)
        self.solar_eclipse_chart.append(self.actions[Spells.STARFIRE].cast_time)
        self.pulsar_chart.append(self.pulsar_progress)
        self.incarn_active.append(1 if self.in_incarn else 0)

        if self.env_timer.done:
            reward = self.total_damage / self.env_timer.max_time
        else:
            reward = self.calc_reward(curr_state, action, next_state)

        return next_state, reward, self.env_timer.done

 