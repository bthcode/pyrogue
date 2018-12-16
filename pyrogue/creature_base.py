"creatures.py - Pyro creatures"

from util import *
from pyro_items import MeleeAttackType
import pyro_items
import dungeon_features
import astar
import magic
import pprint
import logging
import random

def TryWakeUp(mover, sleeper):
    '''
TODO: all creature moves should trigger this for all
      nearby mobs

    - creature has a sleep count - starts at 1000
    - each time something moves near it, decrement sleep count
        - (20 - distance) * (wakefulness/2*stealth) * 1d20
    '''
    distance = calc_distance( mover.x, mover.y, sleeper.x, sleeper.y)
    if distance > 20:
        return

    D = 20 - distance
    w = sleeper.wakefulness
    s = mover.stealth
    r = d('1d20')
    s_orig = sleeper.sleep_count

    x = D * r * w/(s*4)

    sleeper.sleep_count = max(0, sleeper.sleep_count - x)

    logging.debug("D={0}, w={1}, s={2}, r={3}, x={4}, sleep_count={5}".format(D,w,s,r,x,sleeper.sleep_count))

    if s_orig > 0 and sleeper.sleep_count == 0:
        sleeper.WakeUp()

class Bite(pyro_items.MeleeAttackType):
    ''' Bite Attack '''
    range=1
    name="bite"
    verbs=lang.verbs_bite  # no damage, hit, crit
    verbs_sp=lang.verbs_bite_2p
    damage="1d4"


class Claw(pyro_items.MeleeAttackType):
    ''' Claw Attack '''
    range = 1
    name = "claw"
    verbs = lang.verbs_claw
    verbs_sp = lang.verbs_claw_2p
    damage = "1d4"


class AI(object):
    "Artificial intelligence for mobs."

    def __init__(self, mob):
        self.mob = mob


class Berserker(AI):
    """
    This AI routine wanders aimlessly until it sees the @.  Then it charges
    and fights to the death.
    """

    def __init__(self, mob):
        AI.__init__(self, mob)
        self.target = None
        self.tx, self.ty, self.dir = None, None, None
        self.state = "wander"

    def Update(self):
        "Take one action"
        pc = Global.pc
        if self.mob.sleep_count > 0:
            self.mob.Walk(0,0)
            return
        #TODO: Generalize this to follow any mob, not just PC.
        if self.state  == "wander":
            if self.dir  == None:
                self.PickNewDirection()

            if self.mob.can_see_pc:
                self.state = "chase"
                return
            else:
                blocker = self.mob.SquareBlocked(self.mob.x+self.dx, self.mob.y+self.dy)
                if blocker is None:
                    self.mob.Walk(self.dx, self.dy)
                    return
                # The square is blocked; see if it's an openable door:
                if isinstance(blocker, dungeon_features.Door):
                    if self.mob.can_open_doors:
                        if not blocker.Open(self.mob):
                            # Tried and failed to open the door; waste some time:
                            self.mob.Walk(0, 0)
                        return
                self.PickNewDirection()
                return
        elif self.state  == "chase":
            if adjacent(self.mob, pc):
                self.mob.Attack(pc)
                return
            elif self.mob.can_see_pc:
                self.tx, self.ty = pc.x, pc.y
                if self.mob.CanAttack(pc):
                    walk_or_attack = weighted_choice( [('Walk', 1), ('Attack', 3)] )
                    if walk_or_attack  == 'Attack':
                        self.mob.Attack(pc)
                        return
            else:
                if (self.mob.x, self.mob.y)  == (self.tx, self.ty):
                    # We're at the last place we saw the @, and we still can't see him:
                    self.state = "wander"
                    return
            # We can see the PC, but are not in melee range: use A*:
            path = astar.path(self.mob.x, self.mob.y, self.tx, self.ty,
                              self.mob.PathfindPass, max_length = 10)
            if path:
                dx, dy = path[0][0] - self.mob.x, path[0][1] - self.mob.y
                self.mob.Walk(dx, dy)
                return
            else:
                # Pathfinding failed, but we can see the @...just sit there and be mad:
                self.mob.Walk(0, 0)
                return

    def PickNewDirection(self):
        try:
            self.dir = choice([d for d in range(9) if d != 4
                              and not self.mob.SquareBlocked(
                                  self.mob.x+offsets[d][0],
                                  self.mob.y+offsets[d][1])])
            self.dx, self.dy = offsets[self.dir]
            return True
        except IndexError:
            # No options for movement:
            self.mob.Walk(0, 0)
            return False


class Creature(object):
    """An animate object.

    Attributes:
        hp_max
        hp
        mp_max
        mp
        tile : for drawing
        rarity
        unique
        vision_radius : distance creature can see
        natural_armor : give ProtectionBonus
        level : level in the dungeon
        move_speed : speed
        attack_speed : speed
        cast_speed : speed
        age : for regeneration
        heal_timer : for regeneration
        mana_timer : for regneration
        x : current position
        y : current position
    """
    name = "Generic Creature"   # If this is seen in-game, it's a bug.
    hp_max = 10
    mp_max = 0
    hp = hp_max
    mp = mp_max
    tile = "@"
    color = c_Magenta
    AIType = Berserker
    unique = False
    dead = False
    level = 9999    # By default won't be generated
    rarity = 1.0
    natural_armor = 0
    vision_radius = 8
    free_motion = False
    friendly = False
    age = 0  # Strictly increasing timer for effect durations, regeneration, etc.
    heal_timer = 0
    mana_timer = 0 # For regeneration
    can_open_doors = False
    is_pc = False
    can_see_pc = False
    pc_can_see = False

    # resistance and such
    wakefulness = 20
    stealth     = 20  # 0:100 - higher is stealthier
    magic_resistance = 20
    fire_resistance = 0
    ice_resistance = 0
    electricity_resistance = 0

    def __init__(self):
        self.effects = []
        self.equipped, self.unequipped = [], []   # By default, no equip slots
        self.x, self.y, self.current_level = 0, 0, None
        self.stats = Stats()
        self.inventory = Inventory(self)
        if self.AIType:
            self.AI = self.AIType(self)
        self.move_speed = 100
        self.attack_speed = 100
        self.cast_speed = 100
        # Sleep and Stealth
        self.sleep_count = 1000
        self.magic_speed_modifier = 0

        # Confusion
        self.is_confused = False
        self.hp = self.hp_max
        self.kill_xp = int(max(self.level+1, 1.5 ** self.level))
        if not self.is_pc:
            # For now, have every mob drop a level-appropriate item:
            self.inventory.Pickup(pyro_items.random_item(int_range(self.level, self.level/4.0, 2)))

    def to_dict(self):
        d = {}
        for attr in ['name', 'color', 'hp', 'hp_max', 'level', 'can_see_pc', 'x', 'y',
                     'move_speed', 'attack_speed', 'cast_speed', 'kill_xp']:
            d[attr] = getattr(self, attr)
        return d

    def AdjustDamageForEffect(self, amount, damage_type=None, source=None):
        logging.debug("creature {1} damage_type={0}".format(damage_type, self.name))
        msg = None
        if damage_type == 'electricty':
            if self.electricity_resistance == 100:
                amount = 0
                msg = "The {0} is unharmed by elecricty".format(self.name)
            elif self.electricty_resistance:
                amount = amount * (self.electricity_resistance/100.)
                msg = "The {0} resists electricity".format(self.name)
            else:
                msg = "The {0} is shocked".format(self.name)
        elif damage_type == 'ice':
            if self.ice_resistance == 100:
                logging.debug("immune ice")
                amount = 0
                msg = "The {0} is unharmed by ice".format(self.name)
            elif self.ice_resistance:
                logging.debug("resist ice")
                amount = amount * (self.ice_resistance / 100. )
                msg = "The {0} resists ice".format(self.name)
            else:
                logging.debug("ice full damage")
                msg = "The {0} is frozen".format(self.name)
        elif damage_type == 'fire':
            logging.debug("creature {0} fire resistance = {1}".format(self.name, self.fire_resistance))
            if self.fire_resistance == 100:
                amount = 0
                msg = "The {0} is unharmed by fire".format(self.name)
                logging.debug("creature immune fire")
            elif self.fire_resistance > 0:
                logging.debug("creature partial fire")
                amount = amount * (self.fire_resistance / 100. )
                msg = "The {0} resists fire".format(self.name)
            else:
                logging.debug("creature full fire")
                msg = "The {0} is burned".format(self.name)
        elif damage_type == 'sleep':
            self.sleep_count = 1000
            msg = "The {0} is asleep".format(self.name)

        if msg:
            Global.IO.Message(msg)

        return amount

    def Attack(self, target):
        ''' TODO: combine melee item into attacks
            TODO: factor confusion in'''
        range_to_target = calc_distance(self.x, self.y, target.x, target.y)
        attacks = [ x for x in self.attacks if x[0].range >= range_to_target ]
        if not len(attacks):
            self.Delay(self.GetMoveSpeed())
            return
        attack = weighted_choice(attacks)
        if isinstance(attack, magic.Spell) and self.is_confused:
            Global.IO.Message("The {0} tries to cast a spell, but is confused".format(self.name))
        elif isinstance(attack, magic.Spell):
            attack.Attempt(self, target)
            self.Delay(self.GetCastSpeed())
        else:
            success = attack.Attempt(self, target)

    def GetPathToTarget(self, target):
        return linear_path(self.x, self.y, target.x, target.y,
                           self.current_level.BlocksPassage)

    def CanAttack(self, target):
        ''' Range test '''
        range_to_target = calc_distance(self.x, self.y, target.x, target.y)
        for attack in self.attacks:
            if attack[0].range >=  range_to_target:
                return True
        return False

    def CanOccupyTerrain(self, terrain):
        "Return whether the mob can enter a square with the given terrain."
        if terrain  == FLOOR:
            return True
        return False

    def Delay(self, amount):
        "Add the specified amount of delay to the creature."
        self.timer +=  delay(amount)
        self.age +=  delay(amount)

    def Die(self):
        # Creature has been reduced to <= 0 hp, or otherwise should die:
        self.inventory.DropAll()
        self.current_level.RemoveCreature(self)
        self.dead = True

    def eSTR(self):
        "Return the excess strength stat."
        return int(self.stats("str") - ceil(self.inventory.TotalWeight()))

    def EvasionBonus(self):
        return min(self.eSTR(), self.RawEvasionBonus())

    def FailedMove(self, mob):
        # Something tried to move onto the mob; initiate an attack:
        mob.TryAttack(self)

    def ChangeSpeed(self, amount):
        self.magic_speed_modifier = self.magic_speed_modifier + amount

    def GetAttackSpeed(self):
        return min(max(50, self.attack_speed + self.magic_speed_modifier), 200)

    def GetMoveSpeed(self):
        return min(max(50, self.move_speed + self.magic_speed_modifier), 200)

    def GetCastSpeed(self):
        return min(max(50, self.cast_speed + self.magic_speed_modifier), 200)

    def Heal(self, amount):
        "Heal the creature for the given amount."
        # Can be overridden for creatures that respond differently to healing (undead etc)
        heal_amount = min(amount, self.hp_max - self.hp)
        self.hp_max +=  heal_amount
        return heal_amount

    def ItemInSlot(self, equip_slot):
        "Return the *first* item equipped in the slot, or None if none."
        # Not ideal for slots that can be duplicated (e.g. finger)
        try:
            return self.ItemsInSlot(equip_slot)[0]
        except IndexError: return None

    def ItemsInSlot(self, equip_slot):
        "Return the item(s) currently equipped in a given slot as a (possibly empty) list."
        return [item for item in self.equipped if item.equip_slot  == equip_slot]

    def MeleeDamageBonus(self):
        str_bonus = self.stats("str") - 8
        try:
            weapon_bonus = self.ItemsInSlot(lang.equip_slot_meleeweapon)[0].damage_bonus
        except IndexError:
            # Nothing is wielded.  Maybe include some monk/karate bonus here someday.
            weapon_bonus = 0
        return str_bonus + weapon_bonus

    def MeleeHitBonus(self):
        dex_bonus = self.stats("dex") - 8
        try:
            weapon_bonus = self.ItemsInSlot(lang.equip_slot_meleeweapon)[0].hit_bonus
        except IndexError:
            # Nothing is wielded.  Maybe include some monk/karate bonus here someday.
            weapon_bonus = 0
        confusion_factor = 0
        if self.is_confused:
            confusion_factor = -8
        return dex_bonus + weapon_bonus + confusion_factor

    def MissileHitBonus(self):
        # For now it's the same as melee:
        return self.MeleeHitBonus()

    def Name(self):
        return self.name

    def PathfindPass(self, x, y):
        "Return whether the square is passable for the pathfinder."
        b = self.SquareBlocked(x, y)
        return (b is None) or (isinstance(b, dungeon_features.Door) and self.can_open_doors)

    def ProtectionBonus(self):
        return (self.natural_armor + sum([a.armor_points for a in self.equipped])) / 10.0

    def Quaff(self, potion):
        "Quaff a potion."
        potion.Quaff(self)

    def RawEvasionBonus(self):
        return self.stats("dex") - 8

    def Regenerate(self):
        "See if the creature heals any hp/mp."
        if self.age >= self.heal_timer:
            turns = 30 - self.stats("str")
            self.heal_timer = self.age + 1000 * turns
            if self.hp < self.hp_max:
                self.hp +=  1
            if self.hp > self.hp_max:
                self.hp -=  1
        if self.age >=  self.mana_timer:
            turns = 30 - self.stats("int")
            self.mana_timer = self.age + 1000 * turns
            if self.mp < self.mp_max:
                self.mp +=  1
            if self.mp > self.mp_max:
                self.mp -=  1

    def RemoveEffect(self, effect):
        "Remove an effect from the mob if it's still there."
        try:
            self.effects.remove(effect)
            effect.Remove(self, silent = True)
        except ValueError:
            # It wasn't there.
            pass

    def SquareBlocked(self, x, y):
        "Return the first thing, if any, blocking the square."
        L = self.current_level
        if not (0 < x < L.layout.level_width-1
        and 0 < y < L.layout.level_height-1):
            # Can't occupy squares outside the level no matter what:
            return OUTSIDE_LEVEL
        # Check whether another creature is there:
        c = L.CreatureAt(x, y)
        if c: return c
        # Check whether the terrain type is passable:
        terrain = L.layout.data[y][x]
        if not self.CanOccupyTerrain(terrain):
            return WALL
        # Check whether there's an impassable feature (e.g. closed door):
        feature = L.FeatureAt(x, y)
        if feature and not self.CanOccupyTerrain(feature.block_type):
            return feature
        return None



    def TakeDamage(self, amount, damage_type=None, source=None):
        logging.debug("TakeDamage, type={0}".format(damage_type))
        if self.sleep_count:
            self.WakeUp()
        # This method can be overridden for special behavior (fire heals elemental, etc)
        self.AdjustDamageForEffect(amount, damage_type, source)

        self.hp -=  amount
        # Check for death:
        if self.hp <=  0:
            self.Die()
            if source is Global.pc:
                Global.pc.GainXP(self.kill_xp)

        return amount

    def ResistMagic(self, caster, effect):
        '''
        caster level
        caster magic power
        level
        resists_fire
        immune_fire
        magic_resistance
        '''
        cl = caster.level
        tl = self.level
        d1 = cl * d('1d20')
        d2 = tl * d('1d20')
        logging.debug('cl: {0}, t1: {1}, d1: {2}, d2: {3}'.format(cl, tl, d1, d2))
        if d1 > d2:
            logging.debug('no resist')
            return False
        else:
            logging.debug('resist')
            return True

    def TakeEffect(self, new_effect, duration):
        "Apply a temporary or permanent effect to the creature."
        # TODO - resistance framework
        if duration is None:
            new_effect.expiration = None
        else:
            new_effect.expiration = self.age + duration
        # First remove any effect that is overridden by the new one:
        overridden = [e for e in self.effects if new_effect.Overrides(e)]
        for e in overridden: self.RemoveEffect(e)
        # Now check whether an existing effect overrides this one:
        overrides = [e for e in self.effects if e.Overrides(new_effect)]
        if not overrides:
            new_effect.Apply(self)
            self.effects.append(new_effect)

#    def TryWakeUp(self):
#        '''
#    TODO: all creature moves should trigger this for all
#          nearby mobs
#
#        - creature has a sleep count - starts at 1000
#        - each time something moves near it, decrement sleep count
#            - (20 - distance) * (wakefulness/2*stealth) * 1d20
#        '''
#        pc = Global.pc
#        distance_to_pc = calc_distance( pc.x, pc.y, self.x, self.y)
#        if distance_to_pc > 20:
#            return False
#
#        D = 20 - distance_to_pc
#        w = self.wakefulness
#        s = pc.stealth
#        r = d('1d20')
#        s_orig = self.sleep_count
#
#        x = D * r * w/(s*2)
#
#        self.sleep_count = max(0, self.sleep_count - x)
#
#        logging.debug("D={0}, w={1}, s={2}, r={3}, x={4}, sleep_count={5}".format(D,w,s,r,x,self.sleep_count))
#
#        if s_orig > 0 and self.sleep_count == 0:
#            self.WakeUp()
#            return True
#
#        return False

    def Log(self):
        logging.debug(self)
        logging.debug(pprint.pformat(self.to_dict()))

    def TryAttack(self, target):
        # Mob has tried to move onto another mob; possibly attack.
        # This would be the place to abort an attack on a friendly mob, etc.
        # TODO: implement the above so mobs won't attack each other
        # For now it's hacked:
        if self.is_pc or target.is_pc:
            self.Attack(target)

    def Unequip(self, item, silent = False):
        # Unequip the given item if equipped:
        try:
            self.equipped.remove(item)
            self.unequipped.append(item.equip_slot)
            if self.is_pc and not silent:
                Global.IO.Message(lang.msg_you_unequip % lang.ArticleName("the", item))
            item.OnUnequip(self)
            return True
        except ValueError:
            return False


    def Update(self):
        assert not self.dead
        self.UpdateEffects()
        self.Regenerate()
        self.AI.Update()

    def UpdateEffects(self):
        "Update any temporary mods on self or carried pyro_items."
        expired_effects = [e for e in self.effects if e.expiration is not None
                           and e.expiration < self.age]
        for e in expired_effects:
            e.Remove(self)
            self.effects.remove(e)
        # TODO: add item updates too, once that type of effect exists

    def MakeNoise(self):
        for mob in self.current_level.CreaturesInRange(self.x, self.y, 20):
            if mob.sleep_count > 0:
                TryWakeUp(self, mob)

    def Walk(self, dx, dy):
        "Try to move the specified amounts."
        msg = ""
        if dx  == dy == 0:
            self.Delay(self.GetMoveSpeed())
            return True, msg
        if self.is_confused:
            dx = dx * random.choice([-1,1])
            dy = dy * random.choice([-1,1])

        self.MakeNoise()
        blocker = self.SquareBlocked(self.x+dx, self.y+dy)
        if blocker:
            if not self.free_motion or isinstance(blocker, Creature) or blocker  == OUTSIDE_LEVEL:
                # Something blocked the mob from moving--
                try:
                    # Let the blocker respond if it can:
                    msg = blocker.FailedMove(self)
                except AttributeError:
                    pass
                return False, msg
        self.current_level.MoveCreature(self, self.x + dx, self.y + dy)
        self.Delay(self.GetMoveSpeed())
        return True, ""

    def WakeUp(self):
        logging.debug("WakeUp")
        Global.IO.Message("The {0} wakes up".format(self.name))
        self.sleep_count = 0

    def FallAsleep(self):
        logging.debug("Fall Asleep")
        Global.IO.Message("The {0} falls alseep".format(self.name))
        self.sleep_count = 1000

    def Wield(self, item):
        "Wield the item as a melee weapon."
        # If the item we're wielding is stacked, split one off to wield:
        if item.quantity > 1:
            stack = item
            item = self.inventory.Remove(stack, 1)
            self.inventory.Add(item, nostack = True)
        try:
            # TODO: Ask which to replace if dual-wielding:
            wielded = self.ItemsInSlot(lang.equip_slot_meleeweapon)[0]
        except IndexError:
            wielded = None
        if wielded is not None:
            # Unequip the old item:
            self.Unequip(wielded)
            # Remove and re-add it to inventory so it'll stack if it should:
            self.inventory.Remove(wielded)
            self.inventory.Add(wielded)
        # Wield the new weapon:
        self.Equip(item)

    def Equip(self, item, silent = False):
        # Equip the given item if possible:
        if item.equip_slot in self.unequipped:
            self.equipped.append(item)
            self.unequipped.remove(item.equip_slot)
            if self.is_pc and not silent:
                Global.IO.Message(lang.msg_you_equip % lang.ArticleName("the", item))
            item.OnEquip(self)
            return True
        else:
            return False


class Inventory(object):
    "Inventory class for creatures and the player."

    def __init__(self, mob):
        self.mob = mob
        self.items = []
        self.capacity = mob.stats("str") * 10

    def Add(self, item, nostack = False):
        for i, L in self.items:
            if not nostack and i.StacksWith(item):
                i.quantity +=  item.quantity
                letter = L
                break
        else:
            letter = self.NextLetter()
            self.items.append((item, letter))
        return letter

    def CanHold(self, item):
        "Return whether the item can be picked up."
        return item.Weight() + self.TotalWeight() <=  self.Capacity()

    def Capacity(self):
        return self.capacity

    def Drop(self, item, qty = 1):
        dropped = self.Remove(item, qty)
        assert dropped is not None
        # If the item was equipped, unequip it first:
        if item in self.mob.equipped:
            self.mob.Unequip(item)
            text = lang.you_unequip_and_drop_item % lang.ArticleName("the", dropped)
        else:
            text = lang.you_drop_item % lang.ArticleName("the", dropped)
        # Put the item on the floor:
        self.mob.current_level.AddItem(dropped, self.mob.x, self.mob.y)
        return True, text

    def DropAll(self):
        "Drop all inventory pyro_items--e.g. when the mob dies."
        for i in self.items:
            self.Drop(i[0])

    def GetItemByLetter(self, letter):
        pyro_items = [i[0] for i in self.items if i[1] == letter]
        if len(pyro_items) == 0:
            return None
        elif len(pyro_items) == 1:
            return pyro_items[0]
        else:
            raise IndexError

    def Has(self, item):
        "Return whether the item exists in inventory."
        return item in [i[0] for i in self.items]

    def ItemsOfType(self, type, letters = True):
        # Verify valid type:
        assert len([t for t in pyro_items.types if t[0] == type]) != 0
        # Return the list of pyro_items:
        it = [i for i in self.items if i[0].type == type]
        it.sort(key = lambda i: i[0])
        if letters:
            return it
        else:
            return [i[0] for i in it]

    def NextLetter(self):
        "Return the first free letter."
        taken = [item[1] for item in self.items]
        for L in letters:
            if L not in taken:
                return L
        return None

    def Num(self):
        "Number of pyro_items in the inventory."
        return len(self.items)

    def Pickup(self, item, qty = 1):
        # If they want to pick up fewer pyro_items than are there, split stacks:
        no_remove = False
        if qty < item.quantity:
            new_item = item.Duplicate()  # item to be picked up
            item.quantity -=  qty
            new_item.quantity = qty
            no_remove = True
        else:
            new_item = item
        if self.CanHold(new_item):
            # Add to inventory:
            letter = self.Add(new_item)
            # If it's sitting on the floor of a level, remove it from there:
            if not no_remove and new_item.current_level is not None:
                new_item.current_level.Dirty(new_item.x, new_item.y)
                new_item.current_level.RemoveItem(new_item)
            return True, lang.you_pick_up_item % (lang.ArticleName("the", new_item), letter)
        else:
            return False, lang.error_too_heavy

    def Remove(self, item, qty = 1):
        "Remove a quantity of an item from inventory, returning the item stack removed."
        new_pyro_items = []
        removed_item = None
        for i in self.items:
            if i[0] == item:
                assert i[0].quantity >= qty  # Can't drop more than we have.
                if i[0].quantity == qty:
                    removed_item = i[0]
                    # If it was equipped, unequip it:
                    self.mob.Unequip(item)
                    continue
                elif i[0].quantity > qty:
                    removed_item = deepcopy(i[0])
                    removed_item.quantity = qty
                    i[0].quantity -=  qty
                    new_pyro_items.append(i)
            else:
                new_pyro_items.append(i)
        self.items = new_pyro_items
        return removed_item

    def TotalWeight(self):
        return sum([i[0].Weight() for i in self.items])


class StatMod(object):
    "A temporary or permanent modification of a stat."

    def __init__(self, amount, desc):
        self.amount, self.desc = amount, desc


class Stat(object):
    "Tracks a single stat."

    def __init__(self, abbr, name, value):
        self.abbr=abbr
        self.name=name
        self.base_value=value
        self.mods=[]

    def BaseValue(self):
        return self.base_value

    def CurrentValue(self):
        return self.base_value + sum([mod.amount for mod in self.mods])

    def Modify(self, amount, desc = "", permanent=False):
        if permanent:
            self.base_value +=  amount
        else:
            mod = StatMod(amount, desc)
            # TODO: Only allow one instance with a given desc
            self.mods.append(mod)
            return mod


class Stats(object):
    "Class to handle stat tracking for creatures."

    def __init__(self, str = 8, dex=8, int=8):
        self.stats = {"str": Stat("str", lang.stat_name_str, str),
                      "dex": Stat("dex", lang.stat_name_dex, dex),
                      "int": Stat("int", lang.stat_name_int, int)}

    def __call__(self, stat, base = False):
        "Enables retrieving stats by: creature.stats('str')"
        try:
            if base:
                return self.stats[stat].BaseValue()
            else:
                return self.stats[stat].CurrentValue()
        except KeyError:
            raise KeyError("Stat must be in %s." % self.stats.keys())

    def Modify(self, stat, amount, desc = "", permanent=False):
        return self.stats[stat].Modify(amount, desc, permanent)

    def Unmodify(self, mod):
        for stat in self.stats.values():
            try:
                stat.mods.remove(mod)
            except ValueError:
                pass


class Humanoid(Creature):
    tile = "h"
    color = c_White

    def __init__(self):
        Creature.__init__(self)
        self.unequipped = [lang.equip_slot_head,
                           lang.equip_slot_torso,
                           lang.equip_slot_hands,
                           lang.equip_slot_waist,
                           lang.equip_slot_feet,
                           lang.equip_slot_finger,
                           lang.equip_slot_finger,
                           lang.equip_slot_neck,
                           lang.equip_slot_back,
                           lang.equip_slot_offhand,
                           lang.equip_slot_meleeweapon,
                           lang.equip_slot_missileweapon,
                           lang.equip_slot_ammo]


class Rodent(Creature):
    tile = "r"
    color = c_yellow


class Kobold(Creature):
    tile = "k"
    color = c_Green

    def __init__(self):
        Creature.__init__(self)
        self.unequipped = [lang.equip_slot_head,
                           lang.equip_slot_torso,
                           lang.equip_slot_hands,
                           lang.equip_slot_waist,
                           lang.equip_slot_feet,
                           lang.equip_slot_finger,
                           lang.equip_slot_finger,
                           lang.equip_slot_neck,
                           lang.equip_slot_back,
                           lang.equip_slot_offhand,
                           lang.equip_slot_meleeweapon,
                           lang.equip_slot_missileweapon,
                           lang.equip_slot_ammo]
