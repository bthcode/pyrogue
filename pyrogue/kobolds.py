from creature_families import *

class WimpyKobold(Kobold):
    name = lang.mob_name_kobold
    can_open_doors = True
    hp_max = 6
    str, dex, int = 2, 6, 3
    level = 1
    attacks = [[pyro_items.Punch("1d3", 100), 1]]
    desc = lang.mob_desc_kobold
    def __init__(self):
        Kobold.__init__(self)
        # Some kobolds carry weapons:
        if irand(0, 10) < 7:
            weapon = weighted_choice([
                (pyro_items.ShortSword(), 1),
                (pyro_items.Dagger(), 2),
                (pyro_items.Club(), 3),
                (pyro_items.Whip(), 0.5)])
            self.inventory.Pickup(weapon)
            self.Equip(weapon)
 
