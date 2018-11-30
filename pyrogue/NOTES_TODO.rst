Features To Develop
===================

- Area Affect Spells
- Monsters with arrows
- Other magic affects - sleep, slow, poison, etc.

Knwon Bugs
==========

- If no monsters found for a given level, crash

MAP Project TODO
================

___ Show stats on left side
___ Map not drawing on first time slice
___ Hack in move to ignore x,y and just use Global.pc.x/y
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
        
    
