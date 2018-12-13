Features To Develop
-------------------

   - resistance framework
   - magic success/fail

Time
----
   
   - 

Sleep
-----
    - Creature has a sleep_count, anything > 0 = asleep
    - Creatures start with sleep_count = 1000 
    - Any time anything moves, it calls Creature::MakeNoise()
        - gets all creatures within a radius
        - calls creature_base.TryWakeUp(mover, sleeper) - decrements sleep_count
        - (20 - distance) * (1d20) * (sleeper.wakefulness/4*mover.stealth)
    - Sleep spells set sleep_count to 1000
    - Damage sets it to 0 (Creature::WakeUp())
    
Knwon Bugs
----------

   - If no monsters found for a given level, crash
   - healing potion doesn't seem to work
   - better effect tracking - track max speed, max hp, etc.


Coding Guide 
------------

Resistance Framework
====================

   - Two things can be resisted:
      - Direct Damage (Fire, Ice, Electricty, Physical) from spell or weapon
      - OtherEffectSpells (Sleep other, slow other, blind other, etc.)
   - Direct Damage (Ex. FireBolt):
      - FireBolt is a BoltSpell with damage_type='fire'
      - Mob casts 'Attempt', player casts 'Cast'
         - 'Creature::TakeDamage()' or 'Player::TakeDamage()'
            - Creature::AdjustDamageForEffect(amount, damage_type, source)
   - EffectSpell (Ex. SleepOther)
      - is a OtherEffectSpell
      - EffectSpell::Duration - returns a duration
      - EffectSpell::Effect - returns an effect (Ex. SleepOtherBuff)
           - Apply
           - Remove
      - Attempt 
           - Calls Creature::TakeEffect(self.Effect(target), self.Duration(target))
               - Effect.Apply(self)
               - adds effect to self.effects
   - Creature::Update
       - Creature::UpdateEffects()
       - Calls Effect::remove(self)
          



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

Painting:
========
    PutTile(x,y,tile,color)
        PutChar(y,x,tile,color)
            self.pad.addstr(y,x,ch, curses.color_pair(attr))

    move(y,x)
        ignore y,x, use player.y, player.x
        self.game.ul_x, self.game.ul_y
        self.pad.refresh(ul_y, ul_x, game win coordinates)

    refresh
        

Monster Attacks:
===============
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
=============
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


