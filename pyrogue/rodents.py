from creature_base import *

class Rat(Rodent):
    name = lang.mob_name_rat
    color = c_yellow
    hp_max = 5
    dex, str = 6, 8
    level = 1
    attacks = [
        [Claw("1d2", 100), 2],
        [Bite("1d3", 100), 1],
    ]
    desc = lang.mob_desc_rat

class GreaterRat(Rodent):
    name = lang.mob_name_greater_rat
    color = c_green
    hp_max = 15
    dex, str = 8, 10
    level = 2
    attacks = [
        [Claw("1d4", 100), 2],
        [Bite("1d5", 100), 1],
    ]
    desc = lang.mob_desc_greater_rat

all_rodents = [ Rat, GreaterRat ]
