from util import *


class Feature(object):
    name = ">>no name<<"
    describe = True
    "Dungeon features (stairs, fountains, doors, etc)."
    block_type = FLOOR  # By default features do not block movement.
    tile = "@"
    color = c_Magenta
    potentially_passable = True

    def __init__(self):
        self.x, self.y, self.current_level = None, None, None


class Door(Feature):
    name = lang.feature_name_door
    describe = False

    def __init__(self):
        Feature.__init__(self)
        self.closed = True
        self.tile = "+"
        self.color = c_yellow
        self.block_type = WALL  # Impassable while closed.

    def Close(self, mob):
        if not mob.can_open_doors:
            return False
        if self.closed:
            if mob is Global.pc:
                Global.IO.Message(lang.error_door_already_closed)
                return False
        else:
            creature = self.current_level.CreatureAt(self.x, self.y)
            if creature:
                if mob is Global.pc:
                    Global.IO.Message(
                        lang.error_door_blocked_by_creature % lang.ArticleName("The", creature))
                return False
            if self.current_level.ItemsAt(self.x, self.y):
                if mob is Global.pc:
                    Global.IO.Message(lang.error_door_blocked_by_item)
                return False
            self.closed = True
            self.tile = "+"
            self.block_type = WALL
            mob.Delay(mob.move_speed)
            self.current_level.Dirty(self.x, self.y)
            if mob is Global.pc:
                Global.IO.Message(lang.you_close_door)
            return True

    def FailedMove(self, mob):
        self.Open(mob)

    def Open(self, mob):
        if mob.can_open_doors and self.closed:
            self.closed = False
            self.tile = "/"
            self.block_type = FLOOR
            # Opening is faster than closing to prevent an open-close dance with mobs
            mob.Delay(mob.move_speed * 1.5)
            if mob == Global.pc:
                Global.IO.Message(lang.you_open_door)
            elif mob.pc_can_see:
                Global.IO.Message(lang.mob_opens_door %
                                  lang.ArticleName("The", mob))
            self.current_level.Dirty(self.x, self.y)
            return True
        return False


class Staircase(Feature):
    color = c_white
    block_type = FLOOR
    name = lang.feature_name_staircase

    def __init__(self, direction):
        Feature.__init__(self)
        self.direction = direction
        if direction == "up":
            self.tile = "<"
            self.name = lang.feature_name_staircase_up
        elif direction == "down":
            self.tile = ">"
            self.name = lang.feature_name_staircase_down
        else:
            raise ValueErrror()

    def Ascend(self, mob):
        if self.direction != "up":
            return False, lang.error_stairs_not_up
        d = self.current_level.dungeon
        # Level the stairs lead to
        L = d.GetLevel(self.current_level.depth - 1)
        mob.current_level.RemoveCreature(mob)
        x, y = L.stairs_down
        L.AddCreature(mob, x, y)
        Global.pyro.game.current_level = L
        Global.FullDungeonRefresh = True
        return True, lang.you_ascend_stairs  # TODO: cleanup

    def Descend(self, mob):
        if self.direction != "down":
            return False, lang.error_stairs_not_down
        d = self.current_level.dungeon
        # Level the stairs lead to
        L = d.GetLevel(self.current_level.depth + 1)
        mob.current_level.RemoveCreature(mob)
        x, y = L.stairs_up
        L.AddCreature(mob, x, y)
        Global.pyro.game.current_level = L
        Global.FullDungeonRefresh = True
        return True, lang.you_descend_stairs  # TODO: cleanup


class TopStairs(Staircase):
    def Ascend(self, mob):
        return False, lang.error_cannot_leave


class SmallFire(Feature):
    color = c_Red
    tile = "#"
    name = "small fire"
