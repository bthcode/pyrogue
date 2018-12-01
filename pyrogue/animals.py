from creature_base import *

class Wolf(Creature):
    name = lang.mob_name_wolf
    tile = "d"
    color = c_White
    hp_max = 7
    level = 2
    str, dex, int = 5, 7, 1
    attacks = [(Bite("1d6", 100), 1)]
    move_speed = 110
    desc = lang.mob_desc_wolf

all_animals = [ Wolf ]
