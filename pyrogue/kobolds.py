from creature_base import *


class small_kobold(Kobold):
    name = "small_kobold"
    tile = "k"
    level = 1
    color = c_Yellow
    can_open_doors = True
    hp_max = 8
    str, dex, int = 14, 6, 3
    move_speed = 110
    desc = """It is a squat and ugly humanoid figure with a canine face."""
    attacks = [[pyro_items.Punch("1d5", 100), 1]]


class kobold(Kobold):
    name = "kobold"
    tile = "k"
    level = 2
    color = c_Green
    can_open_doors = True
    hp_max = 12
    str, dex, int = 14, 6, 3
    move_speed = 110
    desc = """It is a small, dog-headed humanoid."""
    attacks = [[pyro_items.Punch("1d8", 100), 1]]


class kobold_shaman(Kobold):
    name = "kobold_shaman"
    tile = "k"
    level = 3
    color = c_Red
    can_open_doors = True
    hp_max = 11
    str, dex, int = 14, 6, 3
    move_speed = 110
    desc = """It is a kobold dressed in skins and gesturing wildly."""
    attacks = [[pyro_items.Punch("1d8", 100), 1]]


class kobold_archer(Kobold):
    name = "kobold_archer"
    tile = "k"
    level = 4
    color = c_White
    can_open_doors = True
    hp_max = 24
    str, dex, int = 14, 6, 3
    move_speed = 110
    desc = """It is an ugly dog-headed humanoid wielding a bow."""
    attacks = [[pyro_items.Punch("1d9", 100), 1]]


class large_kobold(Kobold):
    name = "large_kobold"
    tile = "k"
    level = 5
    color = c_Blue
    can_open_doors = True
    hp_max = 65
    str, dex, int = 14, 6, 3
    move_speed = 110
    desc = """It is a man-sized figure with the all too recognizable face of a kobold."""
    attacks = [[pyro_items.Punch("1d10", 100), 1]]


all_kobolds = [small_kobold,
               kobold,
               kobold_shaman,
               kobold_archer,
               large_kobold]
