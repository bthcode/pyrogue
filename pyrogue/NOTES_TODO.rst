Features To Develop
===================

- Area Affect Spells
- Monsters with arrows
- Other magic affects - sleep, slow, poison, etc.

Knwon Bugs
==========

- If terminal size is too small, crash
- If no monsters found for a given level, crash

Map Project
===========

- dungeon can't be bigger than the screen

Dungeon
    : has Level
        : has layout = dungeon_gen.Level() # FIXME
        : has layout.level_width, level_height: 
        : has layout.data[x][y]
        : has creatures{} <- key = (x,y)
    
        : Example Function: CreatureAt(x,y)

Creature:
    : has x, y
    : has current_level

Player(creaters.Humanoid)
    : Update() <- prime mover for the game
    : has: x, y

# Where does screen renderring happen?
Level::PaintSquare(x,y)
Level::Display(pov)
    for x in self.width:
        for y in self.height:
            PaintSquare(x,y)

  File "/Users/brian.hone/opensource/pyrogue/pyrogue/dungeons.py", line 315, in Update
    mob.Update()
  File "/Users/brian.hone/opensource/pyrogue/pyrogue/player.py", line 618, in Update
    self.current_level.Display(self)
  File "/Users/brian.hone/opensource/pyrogue/pyrogue/dungeons.py", line 198, in Display
    self.PaintSquare(x, y)
  File "/Users/brian.hone/opensource/pyrogue/pyrogue/dungeons.py", line 282, in PaintSquare
    Global.IO.PutTile(x, y, tile, color)        
  File "/Users/brian.hone/opensource/pyrogue/pyrogue/io_curses.py", line 790, in PutTile
    self.screen.PutChar(y+MESSAGE_LINES, x, tile, color)
  File "/Users/brian.hone/opensource/pyrogue/pyrogue/io_curses.py", line 957, in PutChar
    self.addstr(y, x, ch, attr)                
  File "/Users/brian.hone/opensource/pyrogue/pyrogue/io_curses.py", line 898, in addstr
    self.screen.addstr(y, x, s, self.colors[attr])


New
===
Level::origin_x, origin_y
Level::screen_width, screen_height
