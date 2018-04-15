"creatures.py - Pyro creatures"

from creature_families import *
from humanoids         import *
from imps              import *
from animals           import *
from rodents           import *
from kobolds           import *


all_creatures = []
all_creatures += all_rodents
all_creatures += all_imps
all_creatures += all_animals
all_creatures += all_humanoids



def RandomMob(level):
    "Create and return a mob appropriate to the given dungeon level."
    mobs = [(mob, mob.rarity) for mob in all_creatures if -1 <= level - mob.level <= 1]
    mob = weighted_choice(mobs)
    return mob()
