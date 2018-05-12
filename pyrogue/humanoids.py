from creature_families import *
class scruffy_looking_hobbit(Humanoid):
    name = "scruffy_looking_hobbit"
    tile = "h"
    level = 3
    color = c_Blue
    can_open_doors = True
    hp_max = 9
    str, dex, int = 3, 16, 5
    move_speed = 110
    desc = """ An annoying little hobbit."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class dark_elf(Humanoid):
    name = "dark_elf"
    tile = "h"
    level = 7
    color = c_Green
    can_open_doors = True
    hp_max = 39
    str, dex, int = 12, 16, 16
    move_speed = 110
    desc = """ twisted with evil."""
    attacks = [[pyro_items.Punch("2d6", 80), 1]]
class dark_elven_mage(Humanoid):
    name = "dark_elven_mage"
    tile = "h"
    level = 10
    color = c_Red
    can_open_doors = True
    hp_max = 39
    str, dex, int = 8, 16, 16
    move_speed = 120
    desc = """A dark elven figure, dressed all in black, hurling spells at you."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class dark_elven_warrior(Humanoid):
    name = "dark_elven_warrior"
    tile = "h"
    level = 10
    color = c_Yellow
    can_open_doors = True
    hp_max = 60
    str, dex, int = 16, 16, 8
    move_speed = 110
    desc = """A dark elven figure in armour and ready with his sword."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class gnome_mage(Humanoid):
    name = "gnome_mage"
    tile = "h"
    level = 11
    color = c_Red
    can_open_doors = True
    hp_max = 32
    str, dex, int = 8, 14, 16
    move_speed = 110
    desc = """A mage of short stature."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class dark_elven_priest(Humanoid):
    name = "dark_elven_priest"
    tile = "h"
    level = 12
    color = c_Green
    can_open_doors = True
    hp_max = 39
    str, dex, int = 14, 14, 8
    move_speed = 120
    desc = """ deliver your soul to hell."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class dark_elven_lord(Humanoid):
    name = "dark_elven_lord"
    tile = "h"
    level = 20
    color = c_Red
    can_open_doors = True
    hp_max = 144
    str, dex, int = 16, 16, 16
    move_speed = 120
    desc = """A dark elven figure in armour and radiating evil power."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class dark_elven_druid(Humanoid):
    name = "dark_elven_druid"
    tile = "h"
    level = 25
    color = c_Green
    can_open_doors = True
    hp_max = 210
    str, dex, int = 15, 14, 12
    move_speed = 120
    desc = """A powerful dark elf, with mighty nature-controlling enchantments."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class mind_flayer(Humanoid):
    name = "mind_flayer"
    tile = "h"
    level = 28
    color = c_Blue
    can_open_doors = True
    hp_max = 132
    str, dex, int = 14, 14, 16
    move_speed = 110
    desc = """  Claws reach out for you and you feel a presence invade your mind."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class dark_elven_sorcerer(Humanoid):
    name = "dark_elven_sorcerer"
    tile = "h"
    level = 41
    color = c_Red
    can_open_doors = True
    hp_max = 700
    str, dex, int = 12, 18, 18
    move_speed = 130
    desc = """ his slender frame."""
    attacks = [[pyro_items.Punch("1d3", 80), 1],[magic.LightningBall(), 1]]
class Ranger(Humanoid):
    name = "Ranger"
    tile = "h"
    level = 2
    color = c_Blue
    can_open_doors = True
    hp_max = 8
    str, dex, int = 16, 18, 8
    move_speed = 100
    desc = """ Bad aragorns."""
    attacks = [[pyro_items.Punch("1d3", 80), 1],[magic.MagicMissile(), 1] ]
class Archer(Humanoid):
    name = "Archer"
    tile = "h"
    level = 2
    color = c_Blue
    can_open_doors = True
    hp_max = 8
    str, dex, int = 16, 18, 8
    move_speed = 100
    desc = """ Bad aragorns."""
    attacks = []
    def __init__(self):
        Humanoid.__init__(self)
        bow = pyro_items.ShortBow()
        self.inventory.Pickup(bow)
        self.Equip(bow)
        arrow = pyro_items.WoodArrow()
        self.inventory.Pickup(arrow)
        self.Equip(arrow)

all_humanoids = [scruffy_looking_hobbit,dark_elf,dark_elven_mage,dark_elven_warrior,gnome_mage,dark_elven_priest,dark_elven_lord,dark_elven_druid,mind_flayer,dark_elven_sorcerer,Ranger,Archer,]
