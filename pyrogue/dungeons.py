"dungeons.py - Dungeon code for Pyro"

from util import *
import dungeon_gen
import fov
import creatures
import dungeon_features
import random
from io_curses import *


class Dungeon(object):
    "An entire multilevel dungeon."
    def __init__(self, name="dungeon"):
        self.name = name
        self.levels = dict()

    def GetLevel(self, i):
        "Returns a Level object for the i'th level of this dungeon."
        try:
            return self.levels[i]
        except KeyError:
            self.levels[i] = self.NewLevel(i)
            return self.levels[i]

    def NewLevel(self, i):
        "Generate the i'th level of the dungeon."
        L = Level(self, i)
        return L


class Level(object):
    "A single level of a dungeon."
    def __init__(self, dungeon, depth):
        self.timer = 0
        self.dungeon, self.depth = dungeon, depth
        self.creatures = {}
        self.items = {}
        self.features = {}
        self.mob_actions = []
        self.dirty = {}
        self.layout = dungeon_gen.Level()
        self.width = self.layout.level_width
        self.height = self.layout.level_height
        self.memento = [[[" ", c_white]] * self.width
                        for i in range(self.height)]
        self._add_doors()
        self._add_stairs()
        self._add_mobs()
        # Add some fire because I promised I would:
        x, y = self.RandomSquare()
        self.AddFeature(dungeon_features.SmallFire(), x, y)
        self.fov = fov.FOVMap(self.width, self.height, self.BlocksVision)

    def _add_doors(self):
        "Remove the door terrain and put door features in its place."
        for x in range(self.layout.level_width):
            for y in range(self.layout.level_height):
                if self.layout.data[y][x] == DOOR:
                    self.layout.data[y][x] = FLOOR
                    self.AddFeature(dungeon_features.Door(), x, y)

    def _add_stairs(self):
        "Add at least one up and one down staircase, not in the same room."
        self.up_room = choice(self.layout.rooms)
        self.down_room = choice([r for r in self.layout.rooms if r != self.up_room])
        x, y, w, h = self.up_room
        i, j = x + irand(1, w - 2), y + irand(1, h - 2)
        if self.depth == 1:
            self.AddFeature(dungeon_features.TopStairs("up"), i, j)
        else:
            self.AddFeature(dungeon_features.Staircase("up"), i, j)
        self.stairs_up = (i, j)
        x, y, w, h = self.down_room
        i, j = x + irand(1, w - 2), y + irand(1, h - 2)
        self.AddFeature(dungeon_features.Staircase("down"), i, j)
        self.stairs_down = (i, j)

    def _add_mobs(self):
        "Add mobs to the level."
        # Add a random number of mobs to each room:
        # (Don't add in the first room of the first level)
        rooms = [room for room in self.layout.rooms
                 if not(self.depth == 1 and room == self.up_room)]
        for (x, y, w, h) in rooms:
            mobs = d("3d2-3")
            for m in range(mobs):
                # Try at most 5 times to find a spot: TODO: ugly
                for n in range(5):
                    i, j = irand(x, x+w-1), irand(y, y+h-1)
                    if not (self.CreatureAt(i, j) or self.FeatureAt(i, j)):
                        mob = creatures.RandomMob(self.depth)
                        self.AddCreature(mob, i, j)
                        break
                else:
                    log("Mob bailout on level %s" % self.depth)

    def AddCreature(self, mob, x, y):
        "Add a mob to the level at position x, y."
        # Make sure the space isn't already occupied by a mob:
        assert not (x, y) in self.creatures  # Can't stack mobs.
        self.creatures[(x, y)] = mob
        mob.x, mob.y, mob.current_level = x, y, self
        if len(self.mob_actions) > 0:
            mob.timer = self.mob_actions[0].timer + irand(1, 1000)
        else:
            mob.timer = 1000
        self.mob_actions.append(mob)
        self.mob_actions.sort(key=lambda m: m.timer)
        self.Dirty(x, y)

    def AddFeature(self, feature, x, y):
        "Add a feature to the level at position x, y."
        assert not (x, y) in self.features  # Can't stack features.
        self.features[(x, y)] = feature
        feature.x, feature.y, feature.current_level = x, y, self
        self.Dirty(x, y)

    def AddItem(self, item, x=None, y=None):
        "Add an item to the level at position x, y."
        if x is None or y is None:
            # Randomly place it somewhere in the level:
            x, y = self.RandomSquare()
            self.items.append(item)
        if (x, y) in self.items:
            # See if there's a stack of this item already; if so, add it:
            for existing_item in self.items[(x, y)]:
                if item.StacksWith(existing_item):
                    existing_item.quantity += item.quantity
                    break
            else:
                # No existing stack to combine with; add this item to the list:
                self.items[(x, y)].append(item)
                item.x, item.y, item.current_level = x, y, self
                self.Dirty(x, y)
        else:
            self.items[(x, y)] = [item]
            item.x, item.y, item.current_level = x, y, self
            self.Dirty(x, y)

    def PushItem(self, item, x, y):
        "Add the item at x, y, pushing existing item(s) out of the way."
        if not (x, y) in self.items:
            # Nothing there; just place it:
            self.items[(x, y)] = [item]
            item.x, item.y, item.current_level = x, y, self
            self.Dirty(x, y)
            return
        # Something there; stack if possible:
        for existing_item in self.items[(x, y)]:
            if item.StacksWith(existing_item):
                existing_item.quantity += item.quantity
                return
        # Something non-stackable is there; push it out of the way:
        self.invalid = [(x, y)]  # list of squares we can't displace to

    def AdjacentSquares(self, x, y):
        "Return coordinates of the 8 adjacent squares to x, y."
        adj = []
        for i in range(x-1, x+2):
            for j in range(y-1, y+2):
                if (0 <= i < self.layout.level_width and
                    0 <= j < self.layout.level_height and
                    not (i == x and j == y)):
                    adj.append((i, j))
        return adj

    def AllCreatures(self):
        return self.creatures.values()

    def BlocksPassage(self, x, y):
        "Return whether the square at (x, y) blocks movement and firing."
        if not (0 <= x < self.layout.level_width and
                0 <= y < self.layout.level_height):
            # Squares outside the level are considered to block passage:
            return True
        if self.layout.data[y][x] == WALL:
            return True
        try:
            if self.FeatureAt(x, y).block_type == WALL:
                return True
        except AttributeError:
            pass
        if self.CreatureAt(x, y):
            return True

    def BlocksVision(self, x, y):
        "Return whether the square at (x, y) blocks vision."
        if not (0 <= x < self.layout.level_width and
                0 <= y < self.layout.level_height):
            # Squares outside the level are considered to block light:
            return True
        if self.layout.data[y][x] == WALL:
            return True
        f = self.FeatureAt(x, y)
        if f and f.block_type == WALL:
            return True
        return False

    def CreatureAt(self, x, y):
        "Return the creature at x, y, if any."
        try:
            return self.creatures[(x, y)]
        except KeyError:
            return None

    def Dirty(self, x, y):
        "Mark the given square as needing to be repainted."
        self.dirty[(x, y)] = True

    def Display(self, pov):
        "Display the level on screen."
        # Display the level:
        painted = 0
        if Global.FullDungeonRefresh:
            Global.FullDungeonRefresh = False
            for x in range(self.width):
                for y in range(self.height):
                    painted += 1
                    self.PaintSquare(x, y)
            log("Full dungeon repaint.")
        else:
            for x, y in self.dirty:
                self.PaintSquare(x, y)
            log("Painted %s dungeon squares." % len(self.dirty))
        self.dirty = {}

    def FeatureAt(self, x, y):
        "Return the feature at x, y, if any."
        try:
            return self.features[(x, y)]
        except KeyError:
            return None

    def IsEmpty(self, x, y):
        "Return true if there is only empty floor at (x, y)."
        return (self.layout.data[y][x] == FLOOR
                and not self.FeatureAt(x, y)
                and not self.CreatureAt(x, y)
                and not self.ItemsAt(x, y))

    def GetCoordsNear(self, x, y):
        r = 2
        while True:
            for i in range(x-r, x+r):
                for j in range(y-r, y+r):
                    if i < 0 or i > self.width:
                        continue
                    if j < 0 or j > self.height:
                        continue
                    if self.IsEmpty(i, j):
                        return i, j
            r += 1

    def GetRandomPosNear(self, x, y, radius):
        attempts = 0
        r = radius
        while True and attempts < 10:
            min_x = max(x-r, 0)
            max_x = min(x+r, self.width-1)
            min_y = max(y-r, 0)
            max_y = min(y+r, self.height-1)
            i = random.randint(min_x, max_x)
            j = random.randint(min_y, max_y)
            if self.IsEmpty(i, j):
                return i, j
            attempts += 1
        return None, None

    def ItemsAt(self, x, y):
        "Return a list of pyro_items at x, y."
        return self.items.get((x, y), [])

    def MoveCreature(self, mob, new_x, new_y):
        "Move the creature to the specified place within the level."
        # Make sure the destination isn't occupied by another mob:
        try:
            if self.creatures[(new_x, new_y)] == mob:
                # Mob is already there; do nothing:
                return
            else:
                raise ValueError("Tried to move a mob where one already was.")
        except KeyError:
            self.Dirty(mob.x, mob.y)
            del self.creatures[(mob.x, mob.y)]
            self.creatures[(new_x, new_y)] = mob
            mob.x, mob.y = new_x, new_y
            self.Dirty(mob.x, mob.y)

    def PaintSquare(self, x, y):
        # Start with the floor tile:
        if self.layout.data[y][x] == WALL:
            tile = "#"
            color = c_white
        elif self.layout.data[y][x] == FLOOR:
            tile = "."
            color = c_white
        else:
            tile = "@"
            color = c_Magenta
        if self.fov.Lit(x, y):
            # Currently visible; display pyro_items/mobs:
            self.memento[y][x] = [tile, color]
            # Check for dungeon features:
            feature = self.FeatureAt(x, y)
            if feature:
                tile, color = feature.tile, feature.color
            # See if there are pyro_items:
            for item in self.ItemsAt(x, y):
                tile, color = item.tile, item.color
            self.memento[y][x] = [tile, color]
            # Check for mobs on the spot:
            mob = self.CreatureAt(x, y)
            if mob:
                tile = mob.tile
                color = mob.color
            if self.memento[y][x][0][0] == ".":
                # Don't remember floor tiles; it makes the FOV more apparent:
                self.memento[y][x] = [" ", c_white]
        else:
            # Not in view; show memento:
            tile, color = self.memento[y][x]
        Global.IO.PutTile(x, y, tile, color)

    def LogAll(self):
        log("Level LogAll:")
        for key, creature in self.creatures.items():
            log("creature at: {0}".format(key))
            creature.Log()

    def RandomSquare(self):
        "Return coords of a non-wall, non-feature, non-corridor square."
        # TODO: rewrite this so it won't lock if the level gets absolutely full
        while True:
            room = choice(self.layout.rooms)
            x = irand(room[0], room[0]+room[2]-1)
            y = irand(room[1], room[1]+room[3]-1)
            if not self.FeatureAt(x, y):
                return x, y

    def RemoveCreature(self, mob):
        "Remove the mob from the level."
        keys = [k for k in self.creatures if self.creatures[k] == mob]
        for k in keys:
            self.Dirty(self.creatures[k].x, self.creatures[k].y)
            del self.creatures[k]
        try:
            self.mob_actions.remove(mob)
        except ValueError:
            pass
        mob.current_level = None

    def RemoveItem(self, item):
        "Remove the item from the level."
        keys = [k for k in self.items if item in self.items[k]]
        # Can't remove non-existant item; item can't be in many places.
        assert len(keys) == 1
        for k in keys:
            self.items[k].remove(item)
            self.Dirty(item.x, item.y)
        item.x, item.y, item.current_level = None, None, None

    def Update(self):
        "Execute a single game turn."
        # Pull off the first mob, update it, stick it back in, sort:
        mob = self.mob_actions[0]
        self.timer = mob.timer
        mob.Update()
        self.mob_actions.sort(key=lambda m: m.timer)
