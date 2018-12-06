Features To Develop
===================

- resistance framework
- sleep
- magic success/fail
- death sequence

Knwon Bugs
==========

- If no monsters found for a given level, crash
- healing potion doesn't seem to work
- better effect tracking - track max speed, max hp, etc.

MAP Project TODO
================

___ Tune map size, number of rooms, etc.
___ better code for menus and messages and such

Painting:
    PutTile(x,y,tile,color)
        PutChar(y,x,tile,color)
            self.pad.addstr(y,x,ch, curses.color_pair(attr))

    move(y,x)
        ignore y,x, use player.y, player.x
        self.game.ul_x, self.game.ul_y
        self.pad.refresh(ul_y, ul_x, game win coordinates)

    refresh
        

Monster Attacks:
    - Monster has array of attacks (weighted)
    - Claw, Punch, etc. 
    - Weapons:
        - OnEquip items inserts item into melee attack
        - MeleeWeapon
        - Bow and such is a MissileWeapon
        - Melee weapon has a melee_attack
           - BowAttackType
           - Chop, Stab, Slash, Lash 
        - Weapons with effects - to do
    - Magic:
        - spells call Attempt
    
    Figure out:
        - Other attacks like breath weapons
        - Weapon Effects
        - Effect Spells + Resistance
        - Attack Speed / Multiple Hits 

Effect Spells:
    - OtherEffectSpell: (parent class)
        - Cast (caster->target)
            - target.TakeEffect(self.Effect(target), self.Duration(targeT))

    - SlowOther:
        - Duration: return 5
        - Effect(return SpeedBuff(-90)

    - Effect: (parent class)
        - Apply
        - Duration
        - Remove

        - Example: SpeedBuff (is a Buff -> is a Effect)
            - Apply(target)
            - Remove(target)
        
        
    - Creature:TakeEffect
        : self.effects = []
        Update:
            UpdateEffects:
                - if expired: e.Remove(self)

Turn order:
==========

Level::Update()
    - Creature::Update()
        - AI::Update()
              - Creature::Walk()
                   - Level::MoveCreature()
                        - self.Dirty(x,y)
                        - self.creatures[(x,y)] = mob
                        - mob.x, mob.y = x, y 
                        - self.Dirty(nex x, new y)
              -- or --
              - Creature::Attack()
                    - attack.Attack()
                        - Global.IO.Message()
                            - curses.getch()

     - Player::Update()
          - self.Walk()
          - creatures.Creature.Walk(x,y)
