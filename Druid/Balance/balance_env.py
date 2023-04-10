from Util.environment import GeneralEnvironment, Resource
from Util.simulation_timer import Timer
from Util.priority_queue import Priority_Queue
from Druid.Balance.balance_talents import Talents
from Druid.Balance.balance_constants import *
from Druid.Balance.balance_spells import *
from Druid.Balance.balance_buffs import *
import json
from random import random

class BalanceDruidEnvironment(GeneralEnvironment):
    def __init__(self, haste, critical_strike, versatility, mastery, main_stat):
        self._base_crit_percent = 5.0
        self._base_mastery_percent = 7.2
        self._point_conversion = 0.9

        super().__init__(haste=haste,
                         critical_strike=critical_strike,
                         versatility=versatility,
                         mastery=mastery,
                         main_stat=main_stat)
        
        with open(r'Druid\Balance\talent_loadout.json', 'r') as f:
            self.talent_loadout = json.load(f)

        self.in_moonkin_form = True

        if self.talent_loadout[Talents.natures_balance]:
            self.astral_power = Resource(0, 100, 1, 2, 50)
        else:
            self.astral_power = Resource(0, 100, 0, 0, 0)

        self.DoTs = []

        # Spells
        self.moonfire = Moonfire()
        self.sunfire = Sunfire()
        self.wrath = Wrath()
        self.starfire = Starfire()
        self.starsurge = Starsurge()

        self.spells = [self.moonfire.name, self.sunfire.name, self.wrath.name, self.starfire.name, self.starsurge.name]

        if self.talent_loadout[Talents.stellar_flare]:
            self.stellar_flare = StellarFlare()
            self.spells.append(self.stellar_flare.name)
        
        if self.talent_loadout[Talents.starfall]:
            self.starfall = Starfall()
            self.spells.append(self.starfall.name)

        if self.talent_loadout[Talents.wild_mushroom]:
            self.wild_mushroom = WildMushroom()
            self.spells.append(self.wild_mushroom.name)

        if self.talent_loadout[Talents.fury_of_elune]:
            self.fury_of_elune = FuryOfElune()

            if self.talent_loadout[Talents.radiant_moonlight]:
                self.fury_of_elune.cooldown -= RADIANT_MOONLIGHT_FOE
            self.spells.append(self.fury_of_elune.name)

        if self.talent_loadout[Talents.incarnation_chosen_of_elune]:
            self.incarnation = IncarnationChosenOfElune()
            self.spells.append(self.incarnation.name)

        elif self.talent_loadout[Talents.celestial_alignment]:
            self.celestial_alignment = CelestialAlignment()
            self.spells.append(self.celestial_alignment.name)


        if self.talent_loadout[Talents.twin_moons]:
            self.moonfire.initial_damage *= 1 + TWIN_MOONS_BUFF

        if self.talent_loadout[Talents.power_of_goldrinn]:
            self._power_of_goldrinn.initial_damage *= self.talent_loadout[Talents.power_of_goldrinn]

        # Non-Action Spells
        self._shooting_star = ShootingStar()
        self._sundered_firmament = SunderedFirmament()
        self._power_of_goldrinn = PowerOfGoldrinn()
        self._astral_smolder = AstralSmolder()

        # Mechanics
        self._in_solar_eclipse = False
        self._in_lunar_eclipse = False

        self._wraths_until_lunar_eclipse = 2
        self._starfires_until_solar_eclipse = 2

        # Buffs
        self.buffs = Priority_Queue()

        self._natures_grace = NaturesGrace(self, name=Talents.natures_grace)
        self._solstice = Solstice(self, name=Talents.solstice)
        self._umbral_embrace = UmbralEmbrace(self, name=Talents.umbral_embrace)
        self._starweavers_weft = StarweaversWeft(self, name="Starweaver's Weft")
        self._starweavers_warp = StarweaversWarp(self, name="Starweaver's Warp")
        self._celestial_alignment = CelestialAlignment(self, name=Talents.celestial_alignment)
        self._incarnation = Incarnation(self, name=Talents.incarnation_chosen_of_elune)
        self._rattle_the_stars = RattleTheStars(self, name=Talents.rattle_the_stars)

        self._sundered_firmament_counter = 0
        self._balance_of_all_things_nature = 0
        self._balance_of_all_things_arcane = 0
        self.umbral_embrace  = False
        self.shooting_star_count = 0
        self.starlord_stacks = 0
        self.primordial_arcanic_pulsar_count = 0
        self.orbit_breaker_count = 0
        
        pass

    def on_enter_eclipse(self):
        if self.talent_loadout[Talents.solstice]:
            SHOOTING_STAR_PROC_CHANCE *= 3
            self.buffs.append((self.env_timer.current_time + SOLSTICE_BUFF_TIME, Talents.solstice))
        return

    def on_leave_eclipse(self):
        if self.talent_loadout[Talents.natures_grace]:
            self.update_haste_percent(0.15)
            self.buffs.append((self.env_timer.current_time + NATURES_GRACE_BUFF_TIME, Talents.natures_grace))
        return

    def on_enter_solar_eclipse(self):
        self.wrath.initial_damage *= 1 + ECLIPSE_WRATH_BUFF

        if not self.on_enter_eclipse: self.on_enter_eclipse = True

        self._in_solar_eclipse = True
        
        if self.talent_loadout[Talents.balance_of_all_things]:
            self._balance_of_all_things_nature = BASE_BOAT_CRIT_BUFF * (1 + self.talent_loadout[Talents.balance_of_all_things])
            self.buffs.append((self.env_timer.current_time + BOAT_DECAY, Talents.balance_of_all_things + " (Nature)"))

        if self.talent_loadout[Talents.umbral_intensity]:
            self.wrath.initial_damage *= 1 + UMBRAL_INTENSITY_WRATH * self.talent_loadout[Talents.umbral_intensity]

        if self.talent_loadout[Talents.stellar_innervation]:
            self.sunfire.astral_power *= 2

        if self.talent_loadout[Talents.soul_of_the_forest]:
            self.wrath.astral_power *= 1 + SOUL_OF_THE_FOREST_WRATH

        if self.talent_loadout[Talents.sundered_firmament]:
            self._sundered_firmament_counter += 1
            
            if self._sundered_firmament_counter % 2 == 0:
                self._sundered_firmament.next_tick = self.calculate_next_dot_tick(self._sundered_firmament)
                self.DoTs.append((self._sundered_firmament.next_tick, self._sundered_firmament.name, self._sundered_firmament.duration+self.env_timer.current_time))
                self._sundered_firmament_counter = 0
        return
    
    def on_leave_solar_eclipse(self, set):
        self.wrath.initial_damage /= 1 + ECLIPSE_WRATH_BUFF

        if not self.on_leave_eclipse: self.on_leave_eclipse = True

        self._in_solar_eclipse = False

        if self.talent_loadout[Talents.umbral_intensity]:
            self.wrath.initial_damage /= 1 + (UMBRAL_INTENSITY_WRATH * self.talent_loadout[Talents.umbral_intensity])

        if self.talent_loadout[Talents.stellar_innervation]:
            self.sunfire.astral_power /= 2

        if self.talent_loadout[Talents.soul_of_the_forest]:
            self.wrath.astral_power /= 1 + SOUL_OF_THE_FOREST_WRATH
        return
    
    def on_enter_lunar_eclipse(self, set):
        if not self.on_enter_eclipse: self.on_enter_eclipse = True
        self._in_lunar_eclipse = True

        if self.talent_loadout[Talents.balance_of_all_things]:
            self._balance_of_all_things_arcane = BASE_BOAT_CRIT_BUFF * (1 + self.talent_loadout[Talents.balance_of_all_things])
            self.buffs.append((self.env_timer.current_time + BOAT_DECAY, Talents.balance_of_all_things + " (Arcane)"))

        if self.talent_loadout[Talents.umbral_intensity]:
            # TODO: Add umbral intensity
            pass

        if self.talent_loadout[Talents.stellar_innervation]:
            self.moonfire.astral_power *= 2
            pass

        if self.talent_loadout[Talents.soul_of_the_forest]:
            # TODO: Add soul of the forest
            pass

        if self.talent_loadout[Talents.sundered_firmament]:
            self._sundered_firmament_counter += 1
            
            if self._sundered_firmament_counter % 2 == 0:
                self._sundered_firmament.next_tick = self.calculate_next_dot_tick(self._sundered_firmament)
                self.DoTs.append((self._sundered_firmament.next_tick, self._sundered_firmament.name, self._sundered_firmament.duration+self.env_timer.current_time))
                self._sundered_firmament_counter = 0

        return
    
    def on_leave_lunar_eclipse(self, set):
        if not self.on_leave_eclipse: self.on_leave_eclipse = True

        self._in_solar_eclipse = False

        if self.talent_loadout[Talents.umbral_intensity]:
            # TODO: Add umbral intensity
            pass

        if self.talent_loadout[Talents.stellar_innervation]:
            self.moonfire.astral_power /= 2

        if self.talent_loadout[Talents.soul_of_the_forest]:
            # TODO: Add soul of the forest
            pass


        return
    
    def on_cast(self, set):
        return
    
    def on_cast_spender(self, set):
        if self.talent_loadout[Talents.starlord]:
            if self.starlord_stacks == 0:
                self.buffs.append((self.env_timer.current_time + STARLORD_BUFF_TIME, Talents.starlord))

            if self.starlord_stacks < MAX_STARLORD_STACKS:
                self.update_haste_percent(-STARLORD_HASTE * self.talent_loadout[Talents.starlord] * self.starlord_stacks)
                self.starlord_stacks += 1
                self.update_haste_percent(STARLORD_HASTE * self.talent_loadout[Talents.starlord] * self.starlord_stacks)

        if self.talent_loadout[Talents.rattle_the_stars]:
            self.rattle_the_stars_count = min(self.rattle_the_stars_count+1, MAX_RATTLE_THE_STARS)
            
            self.starsurge.astral_power = self.starsurge._base_astral_power * (1 - RTS_AP_REDUC * self.rattle_the_stars_count)
            self.starsurge.initial_damage = self.starsurge._base_damage * (1 + RTS_DAMAGE_BUFF * self.rattle_the_stars_count)
            
            self.starfall.astral_power = self.starfall._base_astral_power * (1 - RTS_AP_REDUC * self.rattle_the_stars_count)
            self.starfall.initial_damage = self.starfall._base_damage * (1 + RTS_DAMAGE_BUFF * self.rattle_the_stars_count)
        return
    
    def on_cast_starsurge(self, set):
        if self.starweavers_weft:
            self.starsurge.astral_power = 0

        if self.talent_loadout[Talents.primordial_arcanic_pulsar]:
            self.primordial_arcanic_pulsar_count += self.starsurge._base_astral_power
            if self.primordial_arcanic_pulsar_count > PULSAR_MAX:
                self.primordial_arcanic_pulsar_count %= PULSAR_MAX
                # TODO: Gain 12s of CA

        if self.talent_loadout[Talents.power_of_goldrinn]:
            # TODO: Add Power of Goldrinn
            pass

        if self.talent_loadout[Talents.starweaver]:
            if random() < STARWEAVERS_WARP:
                self.starweavers_warp = True
        return
    
    def on_cast_starfall(self, set):
        if self.starweavers_warp:
            self.starfall.astral_power = 0

        if self.talent_loadout[Talents.primordial_arcanic_pulsar]:
            self.primordial_arcanic_pulsar_count += self.starfall._base_astral_power
            if self.primordial_arcanic_pulsar_count > 600:
                self.primordial_arcanic_pulsar_count %= 600
                # TODO: Gain 12s of CA

        if self.talent_loadout[Talents.aetherial_kindling]:
            if self.moonfire.remaining_duration > 0:
                self.moonfire.remaining_duration = min(self.moonfire.remaining_duration + AETHERIAL_KINDLING_EXTEND, AETHERIAL_KINDLING_MAX)
            if self.sunfire.remaining_duration > 0:
                self.sunfire.remaining_duration = min(self.sunfire.remaining_duration + AETHERIAL_KINDLING_EXTEND, AETHERIAL_KINDLING_MAX)

        if self.talent_loadout[Talents.starweaver]:
            if random() < STARWEAVERS_WEFT:
                self.starweavers_weft = True
        return
    
    def on_cast_generator(self, set):
        return
    
    def on_cast_wrath(self, set):
        if self._wraths_until_lunar_eclipse > 0:
            self._wraths_until_lunar_eclipse -= 1

            if self._wraths_until_lunar_eclipse == 0:
                self.on_enter_lunar_eclipse = True

        if self.umbral_embrace and self._in_solar_eclipse:
            # TODO: Add wrath cast as astral damage
            pass
        return
    
    def on_cast_starfire(self, set):
        return
    
    def on_gain_resource(self, set):
        return
    
    def on_spend_resource(self, set):
        return
    
    def on_astral_damage(self, set):
        if self.talent_loadout[Talents.umbral_embrace]:
            if random() < UMBRAL_EMBRACE_PROC_CHANCE:
                self.umbral_embrace = True
        return
    
    def on_dot_tick(self, set):
        if self.talent_loadout[Talents.shooting_stars]:
            if random() < SHOOTING_STAR_PROC_CHANCE:
                # TODO: Add shooting star damage
                self.on_astral_damage = True
                pass
            pass

        if self.talent_loadout[Talents.denizen_of_the_dream]:
            # TODO: Add Denizen of the dream
            if self.talent_loadout[Talents.friend_of_the_fae]:
                # TODO: Add Friend of the Fae
                pass
            pass
        return
    
    def on_shooting_star(self, set):
        self.astral_power += 2
        # TODO: Add shooting star damage
        self.on_astral_damage = True
        if self.talent_loadout[Talents.orbit_breaker]:
            self.shooting_star_count += 1

            if self.shooting_star_count == 30:
                self.shooting_star_count = 0
                # TODO: Add 80% full moon cast
            pass
        return
    
    def in_celestial_alignment(self, set):
        if self.talent_loadout[Talents.incarnation_chosen_of_elune]:
            # TODO: Add Incarnation: Chosen of Elune
            
            if self.talent_loadout[Talents.elunes_guidance]:
                # TODO: Add Elune's Guidance

                    
                pass
            pass
        return

    def calculate_next_dot_tick(self, dot):
        dot.next_tick = dot.tick_length / (1 + self.haste_percent) + self.env_timer.current_time
        return
    
    def calculate_damage(self, spell):
        damage_mod = 1 + self.versatility_percent
        crit_chance = self.critical_strike_percent
        if self.in_moonkin_form:
            damage_mod += MOONKIN_DAMAGE_BUFF
            self.mastery_percent += LYCARAS_MASTERY_BUFF

        if spell.damage_type == DamageType.NATURE:
            if self.sunfire.remaining_duration > 0:
                damage_mod += self.mastery_percent
            if self._in_solar_eclipse:
                damage_mod += ECLIPSE_NATURE_BUFF
            crit_chance += self._balance_of_all_things_nature

        if spell.damage_type == DamageType.ARCANE:
            if self.moonfire.remaining_duration > 0:
                damage_mod += self.mastery_percent
            if self._in_lunar_eclipse:
                damage_mod += ECLIPSE_ARCANE_BUFF
            crit_chance += self._balance_of_all_things_arcane

        damage = self.main_stat * spell.initial_damage * damage_mod

        if random() < crit_chance:
            damage *= 2

            if spell.name == "Wrath" or spell.name == "Starfire":
                self._astral_smolder.next_tick = self.env_timer + self._astral_smolder.tick_length
                self.DoTs.append((self._astral_smolder.next_tick, self._astral_smolder.name, self._astral_smolder.duration + self.env_timer.current_time))

            
        return damage
