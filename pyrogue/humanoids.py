from creature_families import *

class Goblin(Humanoid):
    tile = "g"
    color = c_green
class WimpyGoblin(Goblin):
    name = lang.mob_name_goblin
    can_open_doors = True
    hp_max = 7
    level = 2
    str, dex, int = 3, 6, 3
    desc = lang.mob_desc_goblin
    def __init__(self):
        Goblin.__init__(self)
        # Goblins always carry weapons:
        weapon = weighted_choice([
            (pyro_items.ShortSword(), 3),
            (pyro_items.Club(), 4),
            (pyro_items.LongSword(), 1)])
        self.inventory.Pickup(weapon)
        self.Equip(weapon)
class Ogre(Humanoid):
    name = lang.mob_name_ogre
    tile = "O"
    color = c_Yellow
    can_open_doors = True
    hp_max = 15
    str, dex, int = 14, 6, 3
    level = 4
    move_speed = 80
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
    desc = lang.mob_desc_ogre
class red_hatted_elf(Humanoid):
    name = "red_hatted_elf"
    tile = "h"
    level = 0
    color = c_Red
    can_open_doors = True
    hp_max = 10
    str, dex, int = 14, 6, 3
    move_speed = 110
    desc = """It's Yuletide and this elf has had a few too many."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class scruffy_looking_hobbit(Humanoid):
    name = "scruffy_looking_hobbit"
    tile = "h"
    level = 3
    color = c_Blue
    can_open_doors = True
    hp_max = 9
    str, dex, int = 14, 6, 3
    move_speed = 110
    desc = """ good tavern."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class dark_elf(Humanoid):
    name = "dark_elf"
    tile = "h"
    level = 7
    color = c_Green
    can_open_doors = True
    hp_max = 39
    str, dex, int = 14, 6, 3
    move_speed = 110
    desc = """ twisted with evil."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
class dark_elven_mage(Humanoid):
    name = "dark_elven_mage"
    tile = "h"
    level = 10
    color = c_Red
    can_open_doors = True
    hp_max = 39
    str, dex, int = 14, 6, 3
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
    str, dex, int = 14, 6, 3
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
    str, dex, int = 14, 6, 3
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
    str, dex, int = 14, 6, 3
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
    str, dex, int = 14, 6, 3
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
    str, dex, int = 14, 6, 3
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
    str, dex, int = 14, 6, 3
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
    str, dex, int = 14, 6, 3
    move_speed = 130
    desc = """ his slender frame."""
    attacks = [[pyro_items.Punch("1d3", 80), 1]]
all_humanoids = [WimpyGoblin, Ogre, red_hatted_elf,scruffy_looking_hobbit,dark_elf,dark_elven_mage,dark_elven_warrior,gnome_mage,dark_elven_priest,dark_elven_lord,dark_elven_druid,mind_flayer,dark_elven_sorcerer,]

