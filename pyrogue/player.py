"player.py - Player character module for Pyro"


import pprint
from util import *
import creatures
import pyro_items
import fov
import magic
import dungeon_features
from io_curses import *


class PlayerCharacter(creatures.Humanoid):
    "The player character."
    tile = "@"
    color = c_White
    can_open_doors = True
    is_pc = True
    AIType = None       # The player makes the calls
    unarmed = pyro_items.Punch()
    xp_rate = 1.0   # 2.0 would need 2x the xp to level, 0.8 would need 20% less
    level, xp = 0, 0
    immortal = False
    prev_x, prev_y = None, None
    can_see_mobs = False
    omniscient = False
    spells, last_spell = [], ""
    friendly = True
    vision_radius = 80
    attacks = []

    def __init__(self):
        Global.pc = self
        # Do generic humanoid creature initialization:
        creatures.Humanoid.__init__(self)
        # Set up bag-based inventory:
        self.bag = pyro_items.SmallBag()
        self.inventory = PlayerInventory(self)
        # Initialize commands:
        self.InitCommands()
        # Let the player customize their character:
        self.name = Global.IO.GetString(lang.prompt_player_name, noblank=True,
                                        pattr=c_yellow, iattr=c_Yellow)

        god = Global.IO.GetChoice(
            [Krol, Dis], lang.prompt_player_god % self.name)
        rprompt = lang.prompt_player_race % self.name
        if god == Krol:
            self.archetype = Global.IO.GetChoice(
                [KrolDwarf, KrolElf, KrolHuman], rprompt)(self)
        elif god == Dis:
            self.archetype = Global.IO.GetChoice(
                [DisDwarf, DisElf, DisHuman], rprompt)(self)

        self.archetype.hp, self.archetype.mp = self.stats(
            "str"), max(0, self.stats("int") - 7)
        self.hp_max, self.mp_max = self.archetype.hp, self.archetype.mp
        self.immune_electricity = self.archetype.immune_electricity
        self.resists_electricity = self.archetype.resists_electricity
        self.immune_ice = self.archetype.immune_ice
        self.resists_ice = self.archetype.resists_ice
        self.immune_fire = self.archetype.immune_fire
        self.resists_fire = self.archetype.resists_fire
        # number of gains needed to go up a notch
        self.gain_str, self.gain_dex, self.gain_int = 1, 1, 1
        self.hp, self.mp = self.hp_max, self.mp_max
        self.move_speed = 100
        self.attack_speed = 100
        self.cast_speed = 100
#        self.protection, self.evasion = 0, 0
        self.GainLevel()    # Gain level 1
        self.running, self.resting = False, False
        self.old_fov, self.new_fov = set(), set()
        self.target = None
        self.current_level = None

    def AdjacentPassableSquares(self):
        "Return a list of adjacent squares the player can move into."
        adj = []
        for dx, dy in offsets:
            if (dx, dy) != (0, 0) and not self.SquareBlocked(self.x+dx, self.y+dy):
                adj.append((self.x+dx, self.y+dy))
            else:
                F = self.current_level.FeatureAt(self.x+dx, self.y+dy)
                if F and F.potentially_passable:
                    adj.append((self.x+dx, self.y+dy))
        return adj

    def AscendStairs(self):
        self.UseStairs("ascend")

    def Attack(self, target):
        "Attack the given creature."
        try:
            attack = self.ItemsInSlot(lang.equip_slot_meleeweapon)[
                0].melee_attack
        except IndexError:
            attack = self.unarmed
        success = attack.Attempt(self, target)

    def AutoRest(self):
        if self.run_count > 100 or self.FullyRested():
            self.resting = False
            Global.IO.Message(lang.msg_done_resting)
            return
        if self.can_see_mobs:
            self.resting = False
            Global.IO.Message(lang.msg_stop_resting_enemy)
            return
        self.run_count += 1
        self.Walk(0, 0)
        if self.run_count % 10 == 0:
            Global.IO.screen.refresh()

    def AutoRun(self):
        self.run_count += 1
        self.ran.append((self.x, self.y))
        mx, my = None, None
        if self.run_count > 1:
            for dx, dy in offsets:
                if ((dx == 0 or dy == 0) and (dx != dy) and (self.x+dx != self.prev_x or self.y+dy != self.prev_y)):
                    F = self.current_level.FeatureAt(self.x+dx, self.y+dy)
                    if isinstance(F, dungeon_features.Door):
                        self.running = False
        if self.can_see_mobs:
            self.running = False
        if self.run_in_room:
            if self.SquareBlocked(self.x+self.run_dx, self.y+self.run_dy):
                self.running = False
            else:
                mx, my = self.run_dx, self.run_dy
        else:
            adj = self.AdjacentPassableSquares()
            adj = [s for s in adj if s not in self.ran and (
                s[0] == self.x or s[1] == self.y)]
            if len(adj) == 1:
                # Only one square we can move to other than the one we were just in:
                mx, my = adj[0][0]-self.x, adj[0][1]-self.y
            else:
                self.running = False
        if self.running:
            self.run_was_in_room = self.run_in_room
            self.run_in_room = False
            for x, y, w, h in self.current_level.layout.rooms:
                if (x <= self.x+mx < x+w) and (y <= self.y+my < y+h):
                    self.run_in_room = True
            if self.run_in_room != self.run_was_in_room and self.run_count > 1:
                self.running = False
                return
            self.Walk(mx, my)
            if True and self.run_count % 1 == 0:
                Global.IO.screen.refresh()

    def BeginAutoRest(self):
        self.resting = True
        self.run_count = 0
        Global.IO.Message(lang.msg_resting, nowait=True)

    def BeginAutoRun(self):
        "Move in the given direction until something interesting happens."
        mdir, dx, dy = Global.IO.GetDirection()
        if mdir is None:
            return False
        if dx == dy == 0:
            self.BeginAutoRest()
            return
        else:
            self.running = True
        self.run_dx, self.run_dy, self.run_count = dx, dy, 0
        self.ran = [(self.x+x, self.y+y)
                    for (x, y) in offsets if x == 0 or y == 0]
        try:
            self.ran.remove((self.x+dx, self.y+dy))
        except ValueError:
            pass
        self.run_in_room = False
        for x, y, w, h in self.current_level.layout.rooms:
            if (x <= self.x+dx < x+w) and (y <= self.y+dy < y+h):
                self.run_in_room = True

    def CastSpell(self):
        spell = Global.IO.GetSpell()
        if spell:
            spell.Cast(self)

    def Cheat(self):

        class Cheat:

            def __init__(self, name, desc, fn):
                self.name, self.desc, self.fn = name, desc, fn

        def cheat_hp():
            self.hp += 1000
            self.mp += 1000

        def cheat_omni():
            self.omniscient = not self.omniscient

        def cheat_level():
            Global.pc.GainXP(Global.pc.xp_for_next_level - Global.pc.xp)

        def cheat_immortal():
            self.immortal = not self.immortal
            if self.immortal:
                Global.IO.Message("You are now immortal and cannot die.")
            else:
                Global.IO.Message("You are once again subject to death.")

        def cheat_pyro_item():
            item = Global.IO.GetMonsterChoice("Item:")
            Global.IO.Message("You asked for a {0}".format(item))
            item_list = [x.__name__ for x in creatures.all_creatures]
            try:
                x, y = self.current_level.GetCoordsNear(self.x, self.y)
                Global.IO.Message(
                    "Creating a {0} at {1}, {2}".format(item, x, y))
                m = getattr(pyro_items, item)()
                self.current_level.AddItem(m, x, y)
            except Exception as err:
                Global.IO.Message("Error creating item")

        def cheat_pyro_items():
            for i in range(20):
                while True:
                    dx, dy = irand(-3, 3), irand(-3, 3)
                    if dx*dx + dy*dy < 16:
                        break
                if self.current_level.IsEmpty(self.x+dx, self.y+dy):
                    lvl = int_range(15, 5, 2)
                    self.current_level.AddItem(
                        pyro_items.random_item(lvl), self.x+dx, self.y+dy)

        def cheat_genocide():
            for c in self.current_level.creatures.values():
                if c is not Global.pc:
                    c.Die()

        def cheat_stat():
            self.GainStatPermanent("any")

        def cheat_teleport():
            self.current_level.Display(self)
            x, y = Global.IO.GetLocation("Teleport where?")
            if x is not None:
                self.current_level.MoveCreature(self, x, y)

        def cheat_smite():
            self.current_level.Display(self)
            x, y = Global.IO.GetLocation("Smite whom?")
            if x is not None:
                c = self.current_level.CreatureAt(x, y)
                if c is not None:
                    c.Die()
                else:
                    Global.IO.Message("There's nothing there to smite!")

        def cheat_free_motion():
            self.free_motion = not self.free_motion
            if self.free_motion:
                Global.IO.Message(
                    "You can now walk through walls and ascend/descend without stairs.")
            else:
                Global.IO.Message(
                    "You are no longer able to walk through solid objects.")

        def cheat_clearout():
            for s in self.current_level.fov.Ball(self.x, self.y, 4, ignore_walls=True):
                self.current_level.layout.data[s[1]][s[0]] = "."
                self.current_level.Dirty(*s)

        def cheat_summon_monster():
            monster = Global.IO.GetMonsterChoice("Monster:")
            Global.IO.Message("You asked for a {0}".format(monster))
            monster_list = [x.__name__ for x in creatures.all_creatures]
            if monster not in monster_list:
                pass
            else:
                x, y = self.current_level.GetCoordsNear(self.x, self.y)
                Global.IO.Message(
                    "Creating a {0} at {1}, {2}".format(monster, x, y))
                m = getattr(creatures, monster)()
                self.current_level.AddCreature(m, x, y)

        def cheat_test():
            magic.MagicMissile().Cast(self)
        cheats = [Cheat("Gain 1000 hit points", "", cheat_hp),
                  Cheat("Toggle omniscience", "", cheat_omni),
                  Cheat("Gain a level", "", cheat_level),
                  Cheat("Toggle immortality", "", cheat_immortal),
                  Cheat("Items from heaven", "", cheat_pyro_items),
                  Cheat("Kill all mobs in level", "", cheat_genocide),
                  Cheat("Stat gain", "", cheat_stat),
                  Cheat("Teleport", "", cheat_teleport),
                  Cheat("Smite a creature", "", cheat_smite),
                  Cheat("Toggle free motion", "", cheat_free_motion),
                  Cheat("Clear nearby walls", "", cheat_clearout),
                  Cheat("Target test", "", cheat_test),
                  Cheat("Summon monster", "", cheat_summon_monster),
                  Cheat("Get Item", "", cheat_pyro_item)]
        choices = []
        letters = 'abcdefghijklmnopqrstuvwxyz'
        for idx, cheat in enumerate(cheats):
            choices.append([letters[idx], cheat.name, cheat.desc])

        chosen = Global.IO.ChoiceWindow(title="Choose a Cheat Code", msg=choices)
        logging.debug("cheat choice={0}".format(chosen))
        if chosen is not None and 0 <= chosen < len(cheats):
            cheats[chosen].fn()

    def CommandList(self):
        Global.IO.CommandList(self)

    def DescendStairs(self):
        self.UseStairs("descend")

    def DetailedStats(self):
        "Show a detailed player stats screen."
        Global.IO.DetailedStats(self)

    def Die(self):
        if self.immortal:
            # Allow the player to refuse death:
            if not Global.IO.YesNo("Really die?"):
                self.hp = self.hp_max
                Global.IO.Message("You refuse to die!")
                return
        s = Global.IO.GetDetailedStats(self)
        t = ["^R^ You Have Died", ""] + s
        Global.IO.MsgWindow(msg=t)
        raise GameOver

    def DropItem(self):
        "Drop an item on the floor."
        item = Global.IO.GetItemFromInventory(self, lang.prompt_drop)
        if item:
            if item.quantity > 1:
                dropqty = Global.IO.GetQuantity(
                    item.quantity, lang.prompt_drop_howmany)
                if dropqty is None:
                    return
            else:
                dropqty = 1
            success, msg = self.inventory.Drop(item, dropqty)
            Global.IO.Message(msg)
            return success

    def EndGame(self):
        if Global.IO.YesNo(lang.prompt_save):
            self.SaveGame()
            raise GameOver
        elif Global.IO.YesNo(lang.prompt_quit):
            raise GameOver

    def EquippedInventory(self):
        Global.IO.DisplayInventory(self, equipped=True)

    def ExamineItem(self):
        "Show a detailed description of an item."
        item = Global.IO.GetItemFromInventory(self, lang.prompt_examine)
        if item is None:
            return False   # Cancelled
        Global.IO.DisplayText(item.LongDescription(), c_yellow)

    def Fire(self):
        "Fire a missile weapon."
        # See if there's an equipped missile weapon:
        bow = self.ItemInSlot(lang.equip_slot_missileweapon)
        if bow is None:
            # No missile weapon equipped:
            Global.IO.Message(lang.error_no_missile_weapon)
            return
        else:
            # A bow (or xbow, sling, blowgun, etc) is equipped, check for ammo:
            ammo = self.ItemInSlot(lang.equip_slot_ammo)
            if ammo is None:
                # No ammo equipped; check for appropriate ammo in inventory:
                ammos = self.inventory.ItemsOfType(
                    lang.itemtype_ammo_or_thrown, letters=False)
                if len(ammos) == 0:
                    # No appropriate ammo carried:
                    Global.IO.Message(lang.error_no_ammo %
                                      lang.ArticleName("your", bow))
                    return
                elif len(ammos) == 1:
                    # Only one carried; auto-equip it:
                    ammo = ammos[0]
                    self.Equip(ammo)
                else:
                    # Multiple valid choices; ask the player for one and equip it:
                    ammo = Global.IO.GetChoice(
                        ammos, lang.prompt_which_ammo, nohelp=True)
                    if ammo is None:
                        return  # Player cancelled ammo choice; cancel fire.
                    self.Equip(ammo)

        # -------- targetting -------- #
        cmd = Global.IO.GetDirectionOrTarget(self, target_range=bow.range)

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
            if self.current_level.BlocksPassage(x, y):
                mob = self.current_level.CreatureAt(x, y)
                if mob:
                    target = mob
                break

        path_clear = cmd.blocked

        Global.IO.AnimateProjectile(
            (actual_path, path_clear), ammo.projectile_char, ammo.color)
        self.Delay(bow.fire_speed)
        if target:
            hit = self.MissileHitBonus()
            evade = target.EvasionBonus()
            differential = hit - evade
            if successful_hit(differential, target.level):
                # Attack hit; calculate damage:
                damage_roll = d(ammo.thrown_damage) + ammo.damage_bonus + \
                    d(bow.fire_damage) + bow.damage_bonus
                protection_roll = quantize(target.ProtectionBonus())
                damage = max(d("1d2"), damage_roll - protection_roll)
                damage_taken = target.TakeDamage(
                    damage, ammo.damage_type, source=self)
                report_combat_hit(self, target, damage_taken,
                                  bow.verbs, bow.verbs_sp)
            else:
                report_combat_miss(self, target, bow.verbs, bow.verbs_sp)

    def FullyRested(self):
        return (True
                and self.hp >= self.hp_max
                and self.mp >= self.mp_max)

    def GainLevel(self):
        if self.level > 0:
            Global.IO.Message(lang.msg_you_gain_level % (self.level+1))
        self.archetype.GainLevel()
        self.xp_for_next_level = self.XPNeeded(self.level + 1)
        if self.level > 1:
            Global.IO.ShowStatus()

    def GainStatPermanent(self, stat):
        if stat == "any":
            while True:
                opts = lang.stat_key_str + lang.stat_key_dex + lang.stat_key_int
                k = Global.IO.Ask("Improve %s:%s, %s:%s, or %s:%s?" %
                                  (lang.stat_key_str.upper(), lang.stat_name_str,
                                   lang.stat_key_dex.upper(), lang.stat_name_dex,
                                   lang.stat_key_int.upper(), lang.stat_name_int),
                                  opts+opts.upper(), c_yellow)
                if k.lower() == lang.stat_key_str:
                    self.GainStatPermanent('str')
                    return
                elif k.lower() == lang.stat_key_dex:
                    self.GainStatPermanent('dex')
                    return
                elif k.lower() == lang.stat_key_int:
                    self.GainStatPermanent('int')
                    return
        if stat == "str":
            if self.gain_str > 0:
                self.gain_str -= 1
            if self.gain_str == 0:
                self.stats.Modify("str", 1, permanent=True)
                adj = lang.word_stronger
                self.gain_str = max(
                    1, int((self.stats("str", base=True)-1) / 4) - 1)
            else:
                adj = lang.word_slightly + " " + lang.word_stronger
        elif stat == "dex":
            if self.gain_dex > 0:
                self.gain_dex -= 1
            if self.gain_dex == 0:
                self.stats.Modify("dex", 1, permanent=True)
                adj = lang.word_agiler
                self.gain_dex = max(
                    1, int((self.stats("dex", base=True)-1) / 4) - 1)
            else:
                adj = lang.word_slightly + " " + lang.word_agiler
        elif stat == "int":
            if self.gain_int > 0:
                self.gain_int -= 1
            if self.gain_int == 0:
                self.stats.Modify("int", 1, permanent=True)
                adj = lang.word_smarter
                self.gain_int = max(
                    1, int((self.stats("int", base=True)-1) / 4) - 1)
            else:
                adj = lang.word_slightly + " " + lang.word_smarter
        else:
            raise ValueError(stat)
        Global.IO.Message(lang.msg_you_feel_improved % adj)

    def GainXP(self, amount):
        self.xp += amount

    def GetTarget(self, target_range=None):
        "Ask the player for a target."
        # TODO:
        # - allow for direction key selection

        # - If target selected, highlight and prompt for enter
        t, p = Global.IO.GetTarget(
            target=self.target, target_range=target_range)
        if isinstance(t, creatures.Creature):
            self.target = t
            return self.target, linear_path(self.x, self.y, self.target.x, self.target.y,
                                            self.current_level.BlocksPassage)
        return t, p

    def InitCommands(self):
        self.commands = []
        self.commands.append(
            Command(lang.cmdname_inventory, 'i', self.Inventory))
        self.commands.append(Command(lang.cmdname_equipment, 'e', self.EquippedInventory))
        self.commands.append(Command(lang.cmdname_pickup, ',g', self.Pickup))
        self.commands.append(Command(lang.cmdname_drop, 'd', self.DropItem))
        self.commands.append(Command(lang.cmdname_wear, 'w', self.Wear))
        self.commands.append(Command(lang.cmdname_unwear, 'W', self.Unwear))
        self.commands.append(Command(lang.cmdname_cast, 'm', self.CastSpell))
        self.commands.append(Command(lang.cmdname_fire, 'f', self.Fire))
        self.commands.append(Command(lang.cmdname_throw, 't', self.Throw))
        self.commands.append(Command(lang.cmdname_quaff, "q", self.Quaff))
        self.commands.append(Command(lang.cmdname_read, "r", self.Read))
        self.commands.append(
            Command(lang.cmdname_targetnext, 9, self.TabTarget))
        self.commands.append(
            Command(lang.cmdname_untarget, "T", self.UnTarget))
        self.commands.append(
            Command(lang.cmdname_autorun, '.', self.BeginAutoRun))
        self.commands.append(
            Command(lang.cmdname_autorest, 'R', self.BeginAutoRest))
        self.commands.append(
            Command(lang.cmdname_examine, 'x', self.ExamineItem))
        self.commands.append(
            Command(lang.cmdname_openclosedoor, 'o', self.OpenCloseDoor))
        self.commands.append(
            Command(lang.cmdname_ascend, '<', self.AscendStairs))
        self.commands.append(
            Command(lang.cmdname_descend, '>', self.DescendStairs))
        self.commands.append(
            Command(lang.cmdname_detailedplayerstats, '@', self.DetailedStats))
        self.commands.append(
            Command(lang.cmdname_message_log, 'M', self.MessageLog))
        self.commands.append(Command(lang.cmdname_help, '?', self.CommandList))
        self.commands.append(Command(lang.cmdname_quit, 'Q', self.EndGame))
        self.commands.append(Command(lang.cmdname_cheat, 'C', self.Cheat))
        self.commands.append(Command(lang.cmdname_save, 's', self.SaveGame))

    def Inventory(self):
        Global.IO.DisplayInventory(self)

    def MessageLog(self):
        Global.IO.MessageLog()

    def OpenCloseDoor(self):
        "Open or close an adjacent door."
        adj = self.current_level.AdjacentSquares(self.x, self.y)
        doors = []
        for x, y in adj:
            F = self.current_level.FeatureAt(x, y)
            if isinstance(F, dungeon_features.Door):
                doors.append(F)
        if len(doors) == 0:
            Global.IO.Message(lang.error_nothing_near_to_openclose)
            return False
        elif len(doors) == 1:
            # Just one door adjacent; open/close it:
            if doors[0].closed:
                doors[0].Open(self)
            else:
                doors[0].Close(self)
        else:
            # Multiple doors nearby; ask the player which to close:
            k, dx, dy = Global.IO.GetDirection()
            if k is None:
                # cancelled
                return
            else:
                door = self.current_level.FeatureAt(self.x+dx, self.y+dy)
                if isinstance(door, dungeon_features.Door):
                    if door.closed:
                        door.Open(self)
                    else:
                        door.Close(self)
                else:
                    Global.IO.Message(lang.error_nothing_there_to_openclose)

    def Pickup(self):
        "Pick up pyro_items(s) at the current position."
        pyro_items = self.current_level.ItemsAt(self.x, self.y)
        if len(pyro_items) == 0:
            Global.IO.Message(lang.error_nothing_here_to_pickup)
            return False
        elif len(pyro_items) == 1:
            i = pyro_items[0]
            if i.quantity > 1:
                qty = Global.IO.GetQuantity(
                    i.quantity, lang.prompt_pickup_howmany % i.Name())
                if qty is None:
                    return False
            else:
                qty = 1
            success, msg = self.inventory.Pickup(pyro_items[0], qty)
            Global.IO.Message(msg)
            return success
        else:
            any_success = False
            for i in pyro_items:
                if i.quantity > 1 or Global.IO.YesNo(lang.prompt_pickup % i.Name()):
                    if i.quantity > 1:
                        qty = Global.IO.GetQuantity(
                            i.quantity, lang.prompt_pickup_howmany % i.Name())
                    else:
                        qty = 1
                    if qty is None or qty == 0:
                        continue
                    success, msg = self.inventory.Pickup(i, qty)
                    any_success = any_success or success
            return any_success

    def Quaff(self):
        "Choose a potion and quaff it."
        potion = Global.IO.GetItemFromInventory(
            self, lang.prompt_quaff, types="!", notoggle=True)
        if potion:
            try:
                potion.Quaff(self)
            except AttributeError:
                Global.IO.Message(lang.error_cannot_drink_item % potion.name)

    def Read(self):
        "Choose a scroll and read it."
        scroll = Global.IO.GetItemFromInventory(
            self, lang.prompt_read, types="?", notoggle=True)
        if scroll:
            try:
                scroll.Read(self)
            except AttributeError:
                Global.IO.Message(lang.error_cannot_read_item % scroll.name)

    def TabTarget(self):
        Global.IO.TabTarget()
        self.tab_targeting = True

    def AdjustDamageForEffect(self, amount, damage_type=None, source=None):
        logging.debug("damage_type={0}".format(damage_type))
        msg = None
        if damage_type == 'electricty':
            if self.immune_electricity:
                amount = 0
                msg = "You are unharmed by elecricty"
            elif self.resists_electricity:
                amount -= amount // 2
                msg = "You resist electricity"
            else:
                msg = "You are shocked"
        elif damage_type == 'ice':
            if self.immune_ice:
                logging.debug("immune ice")
                amount = 0
                msg = "You are unharmed by ice"
            elif self.resists_ice:
                logging.debug("resist ice")
                amount -= amount // 2
                msg = "You resist ice"
            else:
                logging.debug("ice full damage")
                msg = "You are frozen"
        elif damage_type == 'fire':
            if self.immune_fire:
                amount = 0
                msg = "You are unharmed by fire"
            elif self.resists_fire:
                amount -= amount // 2
                msg = "You resist fire"
            else:
                msg = "You are burned"

        #if msg:
        #    Global.IO.Message(msg)

        return amount

    def TakeDamage(self, amount, damage_type=None, source=None):
        amount = self.AdjustDamageForEffect(amount,damage_type,source)
        self.hp -= amount
        return amount

    def Throw(self):
        pass

    def UnTarget(self):
        self.target = None

    def SaveGame(self):
        Global.IO.Message(lang.saving_game.format(self.name + '.pkl'))
        Global.pyro.Save(self.name + '.pkl')

    def Update(self):
        "Called each turn; get the player's action and execute it."
        self.UpdateEffects()
        if self.hp <= 0:
            self.Die()
        self.Regenerate()
        # If the targeted creature is dead, untarget it:
        if self.target and self.target.current_level is None:
            self.target = None
        self.old_fov, self.new_fov = self.new_fov, set()
        # Light up the squares within the PC's vision radius:
        radius_squared = (self.vision_radius + 0.5) ** 2
        for mob in self.current_level.creatures.values():
            mob.can_see_pc, mob.pc_can_see = False, False
        self.can_see_mobs = False
        for i, j in self.current_level.fov.Ball(self.x, self.y, max(self.vision_radius, 9)):
            distance_squared = (i - self.x) ** 2 + (j - self.y) ** 2
            mob = self.current_level.CreatureAt(i, j)
            if distance_squared <= radius_squared:
                self.new_fov.add((i, j))
                if mob not in (None, self):
                    self.can_see_mobs = True
                    mob.pc_can_see = True
            # If there's a mob here, and it's within the mob's vision radius, alert it:
            if mob not in (None, self) and distance_squared <= (mob.vision_radius + 0.5) ** 2:
                mob.can_see_pc = True
        if self.omniscient:
            for i in range(self.current_level.width):
                for j in range(self.current_level.height):
                    self.new_fov.add((i, j))
        self.current_level.fov.UnlightAll()
        for s in self.new_fov:
            self.current_level.fov.SetLit(*s)
        # Any square with an FOV transition should be marked dirty:
        for s in self.old_fov ^ self.new_fov:
            self.current_level.Dirty(*s)
        # Display the current level:
        self.current_level.Display(self)
        # If tab-targeting, draw the path:
        if Global.IO.tab_targeting:
            Global.IO.DrawPathToTarget()
        Global.IO.ShowStatus()
        # See if the player has enough xp to gain a level:
        if self.xp >= self.xp_for_next_level:
            self.GainLevel()
        # Finalize display:
        Global.IO.EndTurn()
        if self.running:
            # If autorunning, don't ask for a command:
            self.AutoRun()
        elif self.resting:
            self.AutoRest()
        else:
            # Get the player's command:
            k = Global.IO.GetKey()
            Global.IO.BeginTurn()
            self.tab_targeting = False
            if k == s:
                self.SaveGame()
            elif k in arrow_offsets:
                dx, dy = arrow_offsets[k]
                self.Walk(dx, dy)
            elif 48 < k < 58:
                # Movement key:
                dx, dy = offsets[k-49]
                self.Walk(dx, dy)
            elif chr(k) in vi_offsets:
                dx, dy = vi_offsets[chr(k)]
                self.Walk(dx, dy)
            # See if the key belongs to another defined command:
            try:
                [c for c in self.commands if k in c.keys][0].function()
            except IndexError:
                pass
            if not self.tab_targeting:
                Global.IO.tab_targeting = False

    def UseStairs(self, action):
        if self.free_motion:
            # Just find some stairs and use them:
            if action == "ascend":
                name = "staircase up"
            elif action == "descend":
                name = "staircase down"
            stairs = [f for f in self.current_level.features.values()
                      if f.name == name][0]
        else:
            stairs = self.current_level.FeatureAt(self.x, self.y)
            if not isinstance(stairs, dungeon_features.Staircase):
                Global.IO.Message(lang.error_no_stairs_here)
                return False
        if action == "ascend":
            success, msg = stairs.Ascend(self)
        elif action == "descend":
            success, msg = stairs.Descend(self)
        else:
            raise ValueError
        Global.IO.Message(msg)

    def Walk(self, dx, dy):
        "Try to move the specified amounts."
        px, py = self.x, self.y
        success, msg = creatures.Creature.Walk(self, dx, dy)
        if msg:
            Global.IO.Message(msg)
        if success:
            self.prev_x, self.prev_y = px, py
            if dx == dy == 0:
                # Don't describe if we didn't actually move:
                return True
            # Describe anything in the square:
            desc = ""
            for i in self.current_level.ItemsAt(self.x, self.y):
                self.running = False    # Stop if we're autorunning
                if desc:
                    desc = lang.msg_several_items_here
                    break
                desc = lang.msg_item_here % lang.ArticleName("a", i)
            f = self.current_level.FeatureAt(self.x, self.y)
            if f:
                self.running = False    # Stop if we're autorunning
                if f.describe and not desc:
                    desc = lang.msg_feature_here % f.name
            if desc:
                Global.IO.Message(desc)
            self.current_level.Display(self)
            return True
        else:
            return False

    def Wear(self):
        "Let the player choose an item to equip."
        item = Global.IO.GetItemFromInventory(self, lang.prompt_wear, types='[="({|',
                                              equipped=False, notoggle=True)
        if item is None:
            return False   # Cancelled
        # Verify that the item can be equipped:
        try:
            item.equip_slot
        except AttributeError:
            Global.IO.Message(lang.error_cannot_equip_item)
            return False
        # If it's already equipped, remove it:
        if self.Unequip(item):
            return False
        # Item isn't equipped; see if there's an open slot:
        if item.equip_slot not in self.unequipped:
            # No slot available; free it up:
            worn = [i for i in self.equipped if i.equip_slot == item.equip_slot]
            if len(worn) == 1:
                self.Unequip(worn[0])
            elif len(worn) == 0:
                Global.IO.Message(lang.error_item_does_not_fit)
                return False
            else:
                # More than one item in that slot; ask which to remove:
                r = Global.IO.GetChoice(
                    worn, lang.prompt_remove_which, nohelp=True)
                if r is None:
                    return False
                self.Unequip(r)
        self.Equip(item)

    def Unwear(self):
        "Let the player choose an item to unequip."
        item = Global.IO.GetItemFromInventory(
            self, lang.prompt_unwear, equipped=True, notoggle=True)
        if item is None:
            return False  # Cancelled
        self.Unequip(item)

    def XPNeeded(self, level):
        "Return the xp needed to attain the given level."
        if level > 1:
            return int(10 * self.xp_rate * 1.5 ** (level-1) + self.XPNeeded(level - 1))
        elif level == 1:
            return 0
        else:
            raise ValueError


class Command(object):
    "Any command the player can give has an instance of this class."
    long_desc = ""

    def __init__(self, desc, keys, function):
        if isinstance(keys, str):
            self.keys = [ord(c) for c in keys]
        elif isinstance(keys, int):
            self.keys = [keys]
        else:
            self.keys = keys
        self.desc, self.function = desc, function


class PlayerInventory(creatures.Inventory):

    def CanHold(self, item):
        return item.Weight() * self.mob.bag.reduction + self.TotalWeight() <= self.Capacity()

    def TotalWeight(self):
        eq = sum([i.Weight() for i in self.mob.equipped])
        pack = sum([i[0].Weight() for i in self.items
                    if i[0] not in self.mob.equipped]) * self.mob.bag.reduction
        return eq + pack


class Diety(object):
    pass


class Krol(Diety):
    name = "Krol"
    desc = lang.goddesc_krol


class Dis(Diety):
    name = "Dis"
    desc = lang.goddesc_dis


class Archetype(object):
    resists_electricity = False
    resists_ice = False
    resists_fire = False
    immune_electricity = False
    immune_ice = False
    immune_fire = False
    def __init__(self, pc):
        self.pc = pc
        self.gain_str, self.gain_dex, self.gain_int, self.gain_any = 0, 0, 0, 0
        # Starting pyro_items common to all archetypes:
        pc.inventory.Pickup(pyro_items.MinorHealPotion())

    def GainLevel(self):
        pc = self.pc
        pc.level += 1
        hp_gain, mp_gain = pc.stats(
            "str", base=True) / 2, max(0, (pc.stats("int", base=True) - 7) / 2)
        self.hp += hp_gain
        pc.hp_max = int(self.hp)
        pc.hp += int(hp_gain)
        self.mp += mp_gain
        pc.mp_max = int(self.mp)
        pc.mp += int(mp_gain)
        if pc.level % 2 == 0:
            # Stat gain at even levels:
            stat, self.stat_gains = self.stat_gains[0], self.stat_gains[1:]
            pc.GainStatPermanent(stat)
            self.stat_gains.append(stat)


class KrolDwarf(Archetype):
    name = lang.archname_kroldwarf
    cname = lang.archname_kroldwarf_short
    desc = lang.archdesc_kroldwarf

    def __init__(self, pc):
        armor = pyro_items.random_armor(-2,
                                        pyro_items.ChainShirt, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = pyro_items.random_melee_weapon(
            0, pyro_items.LongSword, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Equip(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.stats = creatures.Stats(11, 8, 5)
        self.stat_gains = ['str', 'dex', 'any', 'str']


class DisDwarf(Archetype):
    name = lang.archname_disdwarf
    cname = lang.archname_disdwarf_short
    desc = lang.archdesc_disdwarf

    def __init__(self, pc):
        armor = pyro_items.random_armor(-2, pyro_items.Jerkin, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = pyro_items.random_melee_weapon(
            0, pyro_items.ShortSword, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Equip(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.stats = creatures.Stats(8, 8, 8)
        self.stat_gains = ['dex', 'any', 'str', 'any', 'int', 'any']


class KrolElf(Archetype):
    name = lang.archname_krolelf
    cname = lang.archname_krolelf_short
    desc = lang.archdesc_krolelf

    def __init__(self, pc):
        armor = pyro_items.random_armor(-2, pyro_items.Robe, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = pyro_items.random_melee_weapon(
            0, pyro_items.Dagger, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Equip(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.stats = creatures.Stats(5, 7, 12)
        self.stat_gains = ['int', 'any', 'int']
        pc.spells.append(magic.MagicMissile())


class DisElf(Archetype):
    name = lang.archname_diself
    cname = lang.archname_diself_short
    desc = lang.archdesc_diself

    def __init__(self, pc):
        armor = pyro_items.random_armor(-2, pyro_items.Jerkin, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        self.resists_fire = True
        self.immune_ice = True
        weapon = pyro_items.random_melee_weapon(
            0, pyro_items.Dagger, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Equip(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.stats = creatures.Stats(7, 7, 10)
        self.stat_gains = ['int', 'any']
        pc.spells.append(magic.AgilitySpell())
        pc.spells.append(magic.LightningBolt())
        pc.spells.append(magic.IceBolt())
        pc.spells.append(magic.FireBolt())
        pc.spells.append(magic.LightningBall())
        pc.spells.append(magic.IceBall())
        pc.spells.append(magic.FireBall())
        pc.spells.append(magic.Blink())
        pc.spells.append(magic.Teleport())
        pc.spells.append(magic.SlowOther())


class KrolHuman(Archetype):
    name = lang.archname_krolhuman
    cname = lang.archname_krolhuman_short
    desc = lang.archdesc_krolhuman

    def __init__(self, pc):
        armor = pyro_items.random_armor(-2, pyro_items.Jerkin, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = pyro_items.random_melee_weapon(
            0, pyro_items.BattleAxe, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Equip(weapon, silent=True)
        bow = pyro_items.ShortBow()
        pc.inventory.Pickup(bow)
        pc.Equip(bow, silent=True)
        arrow = pyro_items.WoodArrow()
        pc.inventory.Pickup(arrow)
        Archetype.__init__(self, pc)
        pc.stats = creatures.Stats(10, 10, 4)
        self.stat_gains = ['str', 'dex', 'any', 'str', 'dex']


class DisHuman(Archetype):
    name = lang.archname_dishuman
    cname = lang.archname_dishuman_short
    desc = lang.archdesc_dishuman

    def __init__(self, pc):
        armor = pyro_items.random_armor(-2, pyro_items.Jerkin, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = pyro_items.random_melee_weapon(
            0, pyro_items.Dagger, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Equip(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.stats = creatures.Stats(8, 11, 5)
        self.stat_gains = ['dex', 'any', 'dex', 'str']
