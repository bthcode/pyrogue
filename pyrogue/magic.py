"magic.py - Magic spells and effects for Pyro"

from util import *
from io_curses import *
import logging


class Spell(object):
    def AfterCast(self, caster):
        "Called after the spell is finished casting."
        caster.mp -= self.mp_cost
        caster.Delay(caster.cast_speed)

    def CanCast(self, caster):
        if caster.mp < self.mp_cost:
            if caster is Global.pc:
                Global.IO.Message(lang.error_insufficient_mana %
                                  self.name.lower())
            return False
        return True

    def Name(self):
        return self.name


class BoltSpell(Spell):
    "Spells that fire a projectile by line-of-sight toward the target mob."

    def Attempt(self, caster, target):

        path, path_clear = caster.GetPathToTarget(target)

        # Find the first square along the path where there's an obstacle:
        actual_path = []
        for x, y in path[1:]:
            actual_path.append((x, y))
            if caster.current_level.BlocksPassage(x, y):
                # Something here blocks the bolt; see if it's a mob:
                mob = caster.current_level.CreatureAt(x, y)
                if mob:
                    target = mob
                break
        Global.IO.AnimateProjectile(
            (actual_path, path_clear), self.projectile_char, self.projectile_color)
        damage_taken = target.TakeDamage(self.Damage(
            caster), damage_type=self.damage_type, source=caster)
        color = "^Y^"
        if caster is Global.pc:
            self.AfterCast(caster)
            cp = "Your"
            color = "^G^"
        else:
            cp = lang.ArticleName("The", caster) + "'s"
        if target is Global.pc:
            tp = "you"
            color = "^R^"
        else:
            tp = lang.ArticleName("the", target)
        if Global.pc in (caster, target) or caster.pc_can_see or target.pc_can_see:
            Global.IO.Message("%s %s %s%s^0^ %s. [%s%s^0^]" %
                              (cp, self.name.lower(), color, lang.word_hits, tp, color, damage_taken))
        if caster is Global.pc and target.dead:
            Global.IO.Message(lang.combat_you_killed %
                              (lang.ArticleName("the", target), target.kill_xp))

        return True

    def Cast(self, caster):
        '''Cast a ball spell at a target.

        Requirements
            If the user gives a direction, hit the first thing in that direction
            If the user gives a target, hit that first thing along the path

        Args
            caster - the player

        Returns
            None
        '''
        cmd = Global.IO.GetDirectionOrTarget(caster, target_range=self.range)

        if cmd.type == 'x':  # cancel
            return
        elif cmd.type == 't':  # target
            tx = cmd.target.x
            ty = cmd.target.y
        elif cmd.type == 'd':  # direction
            direction = cmd.direction
        else:
            return

        # Find the first square along the path where there's an obstacle or we're at max range
        actual_path = []
        target = None
        for x, y in cmd.path[1:]:
            actual_path.append((x, y))
            tx = x
            ty = y
            if caster.current_level.BlocksPassage(x, y):
                mob = caster.current_level.CreatureAt(x, y)
                if mob:
                    target = mob
                break

        Global.IO.AnimateProjectile(
            (actual_path, path_clear), self.projectile_char, self.projectile_color)
        if target:
            damage_taken = target.TakeDamage(self.Damage(
                caster), damage_type=self.damage_type, source=caster)
            color = "^Y^"
            if caster is Global.pc:
                cp = "Your"
                color = "^G^"
            else:
                cp = lang.ArticleName("The", caster) + "'s"
            if target is Global.pc:
                tp = "you"
                color = "^R^"
            else:
                tp = lang.ArticleName("the", target)
            if Global.pc in (caster, target) or caster.pc_can_see or target.pc_can_see:
                Global.IO.Message("%s %s %s%s^0^ %s. [%s%s^0^]" %
                                  (cp, self.name.lower(), color, lang.word_hits, tp, color, damage_taken))
            if caster is Global.pc and target.dead:
                Global.IO.Message(lang.combat_you_killed %
                                  (lang.ArticleName("the", target), target.kill_xp))
        self.AfterCast(caster)


class AreaEffectSpell(Spell):
    '''Spells that affect an area

Requirements:
    - area affect:
        direction: go until you hit something or end of range
        target: hit the target if visible
    - bolt
        direction: go until you hit something or end of range
        target: go towards target or end of range
    '''

    def Attempt(self, caster, target):
        path, path_clear = caster.GetPathToTarget(target)

        tx = target.x
        ty = target.y
        pts = Global.IO.AnimateAreaEffect(
            tx, ty, self.radius, self.projectile_char, self.projectile_color)
        if len(pts) == 0:
            return
        for pt in pts:
            target = Global.pc.current_level.CreatureAt(pt[0], pt[1])
            # Area affect spells only affect other creatures for now
            if target and target is not caster:
                damage_taken = target.TakeDamage(self.Damage(
                    caster), damage_type=self.damage_type, source=caster)
                color = "^Y^"
                if caster is Global.pc:
                    cp = "Your"
                    color = "^G^"
                else:
                    cp = lang.ArticleName("The", caster) + "'s"
                if target is Global.pc:
                    tp = "you"
                    color = "^R^"
                else:
                    tp = lang.ArticleName("the", target)
                if Global.pc in (caster, target) or caster.pc_can_see or target.pc_can_see:
                    Global.IO.Message("%s %s %s%s^0^ %s. [%s%s^0^]" %
                                      (cp, self.name.lower(), color, lang.word_hits, tp, color, damage_taken))
                if caster is Global.pc and target.dead:
                    Global.IO.Message(lang.combat_you_killed %
                                      (lang.ArticleName("the", target), target.kill_xp))

        self.AfterCast(caster)

        return True

    def Cast(self, caster):
        '''Cast a ball spell at a target.

        Requirements
            If the user gives a direction, hit the first thing in that direction
            If the user gives a target, hit that target

        Args
            caster - the player

        Returns
            None
        '''
        cmd = Global.IO.GetDirectionOrTarget(caster, target_range=self.range)

        tx, ty = caster.x, caster.y

        if cmd.type == 'x':  # cancel
            return
        elif cmd.type == 't':  # target
            tx = cmd.target.x
            ty = cmd.target.y
        elif cmd.type == 'd':  # direction
            direction = cmd.direction
            actual_path = []
            for x, y in cmd.path[1:]:
                actual_path.append((x, y))
                if caster.current_level.BlocksPassage(x, y):
                    break
                tx = x
                ty = y
        else:
            return

        pts = Global.IO.AnimateAreaEffect(
            tx, ty, self.radius, self.projectile_char, self.projectile_color)
        if len(pts) == 0:
            return
        for pt in pts:
            target = Global.pc.current_level.CreatureAt(pt[0], pt[1])
            # Area affect spells only affect other creatures for now
            if target and target is not Global.pc:
                damage_taken = target.TakeDamage(self.Damage(
                    caster), damage_type=self.damage_type, source=caster)
                color = "^Y^"
                if caster is Global.pc:
                    cp = "Your"
                    color = "^G^"
                else:
                    cp = lang.ArticleName("The", caster) + "'s"
                if target is Global.pc:
                    tp = "you"
                    color = "^R^"
                else:
                    tp = lang.ArticleName("the", target)
                if Global.pc in (caster, target) or caster.pc_can_see or target.pc_can_see:
                    Global.IO.Message("%s %s %s%s^0^ %s. [%s%s^0^]" %
                                      (cp, self.name.lower(), color, lang.word_hits, tp, color, damage_taken))
                if caster is Global.pc and target.dead:
                    Global.IO.Message(lang.combat_you_killed %
                                      (lang.ArticleName("the", target), target.kill_xp))
        self.AfterCast(caster)


class TeleportSpell(Spell):
    'spells that move the caster'
    harmful = False

    def Cast(self, caster):
        # 1. find a random spot in radius (will be used for a lot of spells)
        i, j = caster.current_level.GetRandomPosNear(
            caster.x, caster.y, self.radius)
        # 2. move the player there
        if i is not None:
            caster.current_level.MoveCreature(caster, i, j)

    def Attempt(self, caster, target):
        # 1. find a random spot in radius (will be used for a lot of spells)
        i, j = caster.current_level.GetRandomPosNear(
            caster.x, caster.y, self.radius)
        # 2. move the player there
        if i is not None:
            caster.current_level.MoveCreature(caster, i, j)
            Global.IO.Message("%s blinks" % lang.ArticleName("the", caster))


class OtherEffectSpell(Spell):
    "Spells that place a temporary effect on a target"

    def Attempt(self, caster, target):

        path, path_clear = caster.GetPathToTarget(target)

        # Find the first square along the path where there's an obstacle:
        actual_path = []
        for x, y in path[1:]:
            actual_path.append((x, y))
            if caster.current_level.BlocksPassage(x, y):
                # Something here blocks the bolt; see if it's a mob:
                mob = caster.current_level.CreatureAt(x, y)
                if mob:
                    target = mob
                break
        Global.IO.AnimateProjectile(
            (actual_path, path_clear), self.projectile_char, self.projectile_color)
        target.TakeEffect(self.Effect(target), self.Duration(target))
        color = "^Y^"
        if caster is Global.pc:
            self.AfterCast(caster)
            cp = "Your"
            color = "^G^"
        else:
            cp = lang.ArticleName("The", caster) + "'s"
        if target is Global.pc:
            tp = "you"
            color = "^R^"
        else:
            tp = lang.ArticleName("the", target)
        if Global.pc in (caster, target) or caster.pc_can_see or target.pc_can_see:
            Global.IO.Message("%s %s %s%s^0^ %s." %
                              (cp, self.name.lower(), color, "barf", tp, color))
        if caster is Global.pc and target.dead:
            Global.IO.Message(lang.combat_you_killed %
                              (lang.ArticleName("the", target), target.kill_xp))

        return True

    def Cast(self, caster):
        '''Cast a ball spell at a target.

        Requirements
            If the user gives a direction, hit the first thing in that direction
            If the user gives a target, hit that first thing along the path

        Args
            caster - the player

        Returns
            None
        '''
        cmd = Global.IO.GetDirectionOrTarget(caster, target_range=self.range)

        if cmd.type == 'x':  # cancel
            return
        elif cmd.type == 't':  # target
            tx = cmd.target.x
            ty = cmd.target.y
        elif cmd.type == 'd':  # direction
            direction = cmd.direction
        else:
            return

        # Find the first square along the path where there's an obstacle or we're at max range
        actual_path = []
        target = None
        for x, y in cmd.path[1:]:
            actual_path.append((x, y))
            tx = x
            ty = y
            if caster.current_level.BlocksPassage(x, y):
                mob = caster.current_level.CreatureAt(x, y)
                if mob:
                    target = mob
                break

        Global.IO.AnimateProjectile(
            (actual_path, path_clear), self.projectile_char, self.projectile_color)
        if target:
            target.TakeEffect(self.Effect(target), self.Duration(target))
            color = "^Y^"
            if caster is Global.pc:
                cp = "Your"
                color = "^G^"
            else:
                cp = lang.ArticleName("The", caster) + "'s"
            if target is Global.pc:
                tp = "you"
                color = "^R^"
            else:
                tp = lang.ArticleName("the", target)
            if Global.pc in (caster, target) or caster.pc_can_see or target.pc_can_see:
                Global.IO.Message("%s %s %s%s^0^ %s." %
                                  (cp, self.name.lower(), color, "barf", tp))
            if caster is Global.pc and target.dead:
                Global.IO.Message(lang.combat_you_killed %
                                  (lang.ArticleName("the", target), target.kill_xp))
        self.AfterCast(caster)


class SelfBuffSpell(Spell):
    "Spells that confer a temporary effect upon the caster."
    harmful = False

    def Cast(self, caster):
        caster.TakeEffect(self.Effect(caster), self.Duration(caster))


class Effect(object):
    power = 0
    duration = None  # Indicates permanent
    type = "none"
    "Some temporary mod that can apply to creatures, items, etc."

    def Apply(self, target):
        "Make whatever change the effect applies."
        pass    # Implement this in subclass

    def Duration(self, target):
        pass    # Implement this in subclass

    def Overrides(self, other):
        "Return whether this effect should override the other."
        if self.type != other.type:
            return False
        if self.power > other.power:
            return True           # higher power always overrides
        if other.expiration is None:
            return False          # other is permanent; leave it
        if self.expiration is None:
            return True            # this is perm, other isn't; override
        if self.expiration > other.expiration:
            return True  # longer duration, all else equal; override
        return False

    def Remove(self, target, silent=False):
        "Remove the effect from the target."
        pass    # Implement this in subclass


class Buff(Effect):
    "A beneficial effect that targets a creature."
    pass


class EquipStatBonus(Effect):
    "Bonus to a stat gained from equipping an item."

    def __init__(self, item, stat, power):
        self.item, self.stat, self.power = item, stat, power
        self.type = "equip:stat:%s" % stat
        self.desc = "%s %s" % (bonus_str(self.power), self.stat)
        self.name = "%s: %s" % (self.desc, self.item.Name(noweight=True))

    def Apply(self, target, silent=False):
        self.statmod = target.stats.Modify(self.stat, self.power)

    def Duration(self, target):
        return None  # Permanent until item is removed.

    def Remove(self, target, silent=False):
        target.stats.Unmodify(self.statmod)


class DexBuff(Buff):
    name = "Agility"

    def __init__(self, amount=1, desc="Agility"):
        self.power, self.desc = amount, desc

    def Apply(self, target, silent=False):
        self.statmod = target.stats.Modify("dex", self.power)
        if not silent:
            if target is Global.pc:
                Global.IO.Message(lang.effect_agility_buff_you)
            elif target.pc_can_see:
                Global.IO.Message(lang.effect_agility_buff_mob %
                                  lang.ArticleName("The", target))

    def Remove(self, target, silent=False):
        target.stats.Unmodify(self.statmod)
        if not silent:
            if target is Global.pc:
                Global.IO.Message(lang.effect_agility_buff_gone_you)
            elif target.pc_can_see:
                Global.IO.Message(lang.effect_agility_buff_gone_mob %
                                  lang.ArticleName("The", target))


class StrBuff(Buff):
    name = "Might"

    def __init__(self, amount=1, desc="Might"):
        self.amount, self.desc = amount, desc

    def Apply(self, target, silent=False):
        self.statmod = target.stats.Modify("str", self.amount)
        if not silent:
            if target is Global.pc:
                Global.IO.Message(lang.effect_strength_buff_you)
            elif target.pc_can_see:
                Global.IO.Message(lang.effect_strength_buff_mob %
                                  lang.ArticleName("The", target))

    def Remove(self, target, silent=False):
        target.stats.Unmodify(self.statmod)
        if not silent:
            if target is Global.pc:
                Global.IO.Message(lang.effect_strength_buff_gone_you)
            elif target.pc_can_see:
                Global.IO.Message(lang.effect_strength_buff_gone_mob %
                                  lang.ArticleName("The", target))


class SpeedBuff(Buff):
    name = "Speed"

    def __init__(self, amount=1, desc="Speed"):
        self.amount, self.desc = amount, desc

    def Apply(self, target, silent=False):
        logging.debug("Speed Buf Apply target={0}:{1}".format(
            target, target.move_speed))
        target.move_speed = max(1, target.move_speed + self.amount)
        target.attack_speed = max(1, target.attack_speed + self.amount)
        target.cast_speed = max(1, target.cast_speed + self.amount)
        logging.debug("Speed Buf Apply target={0}:{1}".format(
            target, target.move_speed))
        if not silent:
            if target is Global.pc:
                Global.IO.Message(lang.effect_speed_buff_you)
            elif target.pc_can_see:
                Global.IO.Message(lang.effect_speed_buff_mob %
                                  lang.ArticleName("The", target))

    def Remove(self, target, silent=False):
        logging.debug("Speed Buf Remove target={0}:{1}".format(
            target, target.move_speed))
        target.move_speed -= self.amount
        target.attack_speed -= self.amount
        target.cast_speed -= self.amount
        logging.debug("Speed Buf Remove target={0}:{1}".format(
            target, target.move_speed))
        if not silent:
            if target is Global.pc:
                Global.IO.Message(lang.effect_speed_buff_gone_you)
            elif target.pc_can_see:
                Global.IO.Message(lang.effect_speed_buff_gone_mob %
                                  lang.ArticleName("The", target))

class SlowOther(OtherEffectSpell):
    name = "Slow Other"
    shortcut = "wot"
    harmful = True
    level = 1
    mp_cost = 1
    range = 20
    projectile_char, projectile_color = '*', c_Cyan
    desc = "Slow the other guy"

    def Duration(self, target):
        return 1000

    def Effect(self, target):
        return SpeedBuff(-90)


class AgilitySpell(SelfBuffSpell):
    name = lang.spellname_agility
    shortcut = "agi"
    harmful = False
    level = 1
    mp_cost = 3
    desc = lang.spelldesc_agility

    def Duration(self, caster):
        return 10 * 1000

    def Effect(self, caster):
        return DexBuff(2)


class Blink(TeleportSpell):
    name = lang.spellname_blink
    shortcut = 'bnk'
    harmful = False
    range = 999  # affects CanAttack
    level = 2
    mp_cost = 3
    radius = 5
    desc = lang.spelldesc_blink


class Teleport(TeleportSpell):
    name = lang.spellname_teleport
    shortcut = 'tpt'
    harmful = False
    range = 999  # affects CanAttack
    level = 11
    mp_cost = 11
    radius = 999
    desc = lang.spelldesc_teleport


class MagicMissile(BoltSpell):
    name = lang.spellname_magic_missile
    shortcut = lang.spellcode_magic_missile
    harmful = True
    level = 1
    mp_cost = 1
    range = 7
    damage_type = ""   # unresistable
    projectile_char, projectile_color = "-|/\\", c_Red
    desc = lang.spelldesc_magic_missile

    def Damage(self, caster):
        return d("1d3")


class SleepOther(BoltSpell):
    name = "Sleep Other"
    shortcut = "sot"
    harmful = True
    level = 1
    mp_cost = 1
    range = 20
    damage_type = "sleep"
    projectile_char, projectile_color = '*', c_Cyan
    desc = "Make the other guy sleep"

    def Damage(self, caster):
        return 0


class LightningBolt(BoltSpell):
    name = lang.spellname_lightning_bolt
    shortcut = lang.spellcode_lightning_bolt
    harmful = True
    level = 2
    mp_cost = 3
    range = 7
    damage_type = "electricty"
    radius = 1
    projectile_char, projectile_color = '*', c_Cyan
    desc = lang.spelldesc_lightning_bolt

    def Damage(self, caster):
        return d("2d3")


class IceBolt(BoltSpell):
    name = lang.spellname_ice_bolt
    shortcut = lang.spellcode_ice_bolt
    harmful = True
    level = 3
    mp_cost = 5
    range = 7
    damage_type = "ice"
    radius = 1
    projectile_char, projectile_color = '*', c_White
    desc = lang.spelldesc_ice_bolt

    def Damage(self, caster):
        return d("3d3")


class FireBolt(BoltSpell):
    name = lang.spellname_fire_bolt
    shortcut = lang.spellcode_fire_bolt
    harmful = True
    level = 4
    mp_cost = 7
    range = 9
    damage_type = "fire"
    radius = 1
    projectile_char, projectile_color = '*', c_Red
    desc = lang.spelldesc_fire_bolt

    def Damage(self, caster):
        return d("3d3")


class MagicBall(AreaEffectSpell):
    name = lang.spellname_magic_ball
    shortcut = lang.spellcode_magic_ball
    harmful = True
    level = 2
    mp_cost = 3
    range = 5
    damage_type = ""
    radius = 3
    projectile_char, projectile_color = '*', c_Yellow
    desc = lang.spelldesc_magic_ball

    def Damage(self, caster):
        return d("2d3")


class LightningBall(AreaEffectSpell):
    name = lang.spellname_lightning_ball
    shortcut = lang.spellcode_lightning_ball
    harmful = True
    level = 3
    mp_cost = 7
    range = 5
    damage_type = "electricty"
    radius = 3
    projectile_char, projectile_color = '*', c_Cyan
    desc = lang.spelldesc_lightning_ball

    def Damage(self, caster):
        return d("4d3")


class IceBall(AreaEffectSpell):
    name = lang.spellname_ice_ball
    shortcut = lang.spellcode_ice_ball
    harmful = True
    level = 7
    mp_cost = 11
    range = 9
    damage_type = "ice"
    radius = 3
    projectile_char, projectile_color = '*', c_White
    desc = lang.spelldesc_ice_ball

    def Damage(self, caster):
        return d("5d3")


class FireBall(AreaEffectSpell):
    name = lang.spellname_fire_ball
    shortcut = lang.spellcode_fire_ball
    harmful = True
    level = 9
    mp_cost = 15
    range = 11
    damage_type = "fire"
    radius = 3
    projectile_char, projectile_color = '*', c_Red
    desc = lang.spelldesc_fire_ball

    def Damage(self, caster):
        return d("6d3")


# TODO: Method for acquiring new spells
# TODO: Spells that progress by level
# TODO: Dungeon affect spell (stone to mud, light area, beam of light)
# TODO: Monster effect spells (sleep, slow)
