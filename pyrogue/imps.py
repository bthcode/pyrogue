from creature_base import *

class Imp(Creature):
    name = lang.mob_name_imp
    tile = "i"
    color = c_Red
    hp_max = 4
    str, dex, int = 2, 10, 9
    move_speed = 110
    attacks = [(Claw("1d3", 160), 2),(magic.MagicMissile(),1)]
    level = 3
    desc = lang.mob_desc_imp

all_imps = [Imp]
