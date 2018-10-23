import curses
from curses import wrapper
from curses import panel

from util import *

import pyro_items


OPTIMIZE_OUTPUT = True      # Whether to buffer curses output (False won't work yet)
MESSAGE_LINES = 2

# Check what OS we're running under; keycodes differ:
WINDOWS = False
try:
    WINDOWS = 'WCurses' in curses.__version__
except AttributeError:
    pass

ESC = 27
SPC = 32
DEL = 127

tiles = {
    # Terrain/features:
    "floor":            ".",
    "wall":             "#",
    "door_open":        "/",
    "door_closed":      "+",
    "trap":             "^",
    "stairs_up":        "<",
    "stairs_down":      ">",
    "fire":             "#",
    # Mobs:
    "player":           "@",
    "mob":              "x",    # The most generic mob tile, shouldn't be seen
    "ape":              "a",
    "ant":              "a",
    "bat":              "b",
    "centipede":        "c",
    "canine":           "d",
    "dragon":           "D",
    "eye":              "e",
    "feline":           "f",
    "goblin":           "g",
    "golem":            "G",
    "humanoid":         "h",
    "imp":              "i",
    "jelly":            "j",
    "kobold":           "k",
    "lizard":           "l",
    "mold":             "m",
    "ogre":             "O",
    "rodent":           "r",
    "spider":           "s",
    "snake":            "s",
    "troll":            "T",
    "undead":           "z",
    "lurker":           ".",
    "demon":            "&",
    # Items:
    "wand":             "/",
    "ring":             "=",
    "amulet":           '"',
    "stone":            "*",
    "armor":            "[",
    "melee_weapon":     "(",
    "missile_weapon":   "{",
    "tool":             "~",
    "scroll":           "?",
    "book":             "+",
    "potion":           "!",
    "food":             "%",
    "corpse":           "%",
    "ammunition":       "|",
    "money":            "$",
    # Misc:
    "unknown":          ";",
    "blank":            " ",
}

class TargettingCommand:
    mode      = 'x' # x = cancel, t = mob, d = direction
    direction = [0,0]
    target    = None
    path      = []
    blocked   = []




class Menu(object):                                                          

    def __init__(self, items, stdscreen):                                    
        self.window = stdscreen.subwin(0,0)                                  
        self.window.keypad(1)                                                
        self.panel = panel.new_panel(self.window)                            
        self.panel.hide()                                                    
        panel.update_panels()                                                

        self.position = 0                                                    
        self.items = items                                                   
        self.items.append(('exit','exit'))                                   

    def navigate(self, n):                                                   
        self.position += n                                                   
        if self.position < 0:                                                
            self.position = 0                                                
        elif self.position >= len(self.items):                               
            self.position = len(self.items)-1                                

    def display(self):                                                       
        self.panel.top()                                                     
        self.panel.show()                                                    
        self.window.clear()                                                  

        while True:                                                          
            self.window.box()
            self.window.refresh()                                            
            curses.doupdate()                                                
            for index, item in enumerate(self.items):                        
                if index == self.position:                                   
                    mode = curses.A_REVERSE                                  
                else:                                                        
                    mode = curses.A_NORMAL                                   

                msg = '%d. %s' % (index, item[0])                            
                self.window.addstr(1+index, 1, msg, mode)                    

            key = self.window.getch()                                        

            if key in [curses.KEY_ENTER, ord('\n')]:                         
                if self.position == len(self.items)-1:                       
                    break                                                    
                else:                                                        
                    self.items[self.position][1]()                           

            elif key == curses.KEY_UP:                                       
                self.navigate(-1)                                            

            elif key == curses.KEY_DOWN:                                     
                self.navigate(1)                                             

        self.window.clear()                                                  
        self.panel.hide()                                                    
        panel.update_panels()                                                
        curses.doupdate()

   
class IOWrapper(object):
    def __init__(self, stdscr):

        self.more_prompt = " ^Y^%s^0^" % lang.prompt_more
        self.any_key_prompt = "^Y^%s^0^" % lang.prompt_any_key
        self.message_log = []
        self.attack_ticker = []
        self.message_wait = False
        self.tab_targeting = False

        self.stdscr = stdscr
        self.stdscr.clear()
        self.screen = stdscr # FIXME

        curses.initscr()
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(1)
        curses.curs_set(0)

        # Colors
        self.colors = [curses.color_pair(0)]
        for i in range(1, 16):
            curses.init_pair(i, i % 8, 0)
            if i < 8:
                self.colors.append(curses.color_pair(i))
            else:
                self.colors.append(curses.color_pair(i) | curses.A_BOLD)


        # Layout
        self.msg_height    = 3
        self.status_height = 3
        self.stats_width   = 20
        self.height        = None
        self.width         = None
        self.game_height   = None 
        self.game_width    = None 
        self.game_start_y  = None 
        self.game_start_x  = None 
        # TODO: reset these on new level
        self.game_ul_x     = -1
        self.game_ul_y     = -1
        self.calc_layout()

        # Windows
        self.msg_win = curses.newwin(self.msg_height, self.width, 0, 0)
        self.msg_win.addstr(1,1,'msgs')
        self.msg_win.box()
        self.msg_win.refresh()

        self.stats_win = curses.newwin(self.game_height, self.stats_width, self.msg_height, 0)
        self.stats_win.addstr(1,1,'stats')
        self.stats_win.box()
        self.stats_win.refresh()

        self.game_win = curses.newwin(self.game_height, self.game_width, self.msg_height, self.stats_width)
        self.game_win.addstr(1,1,'game')
        self.game_win.refresh()

        self.status_win = curses.newwin(self.status_height, self.width, self.msg_height+self.game_height, 0)
        self.status_win.addstr(1,1,'status')
        self.status_win.box()
        self.status_win.refresh()

    def calc_layout(self):
        self.height, self.width = self.stdscr.getmaxyx()
        self.game_height   = self.height - self.msg_height - self.status_height
        self.game_width    = self.width - self.stats_width 
        self.game_start_y  = self.msg_height 
        self.game_start_x  = self.stats_width 

        self.pad_height = 80
        self.pad_width  = 180
        self.pad = curses.newpad(self.pad_height, self.pad_width)
        #ctr = 0
        #for y in range(0, self.pad_height-1):
        #    for x in range(0, self.pad_width-1):
        #        self.pad.addch(y,x, ord('a') + ctr % 26)
        #        ctr += 1
        #self.ul_x = 0
        #self.ul_y = 0
        #self.move(self.ul_x, self.ul_y)
        curses.doupdate()
        self.pad.touchwin()

    def AnimateProjectile(self, path, char, color):
        "Show a projectile traveling the specified path."
        path, clear = path
        for x, y in path:
            ch = "*"
            self.PutChar(y, x, ch, color)
            animation_delay()
            self.move(Global.pc.y, Global.pc.x)
            #self.pad.refresh()
        for px, py in path: 
            Global.pc.current_level.PaintSquare(px, py)
            self.move(Global.pc.y, Global.pc.x)
            #self.pad.refresh()
    def AnimateAreaEffect(self, tx, ty, radius, char, color):
        '''Show a 'Ball' effect, returning the affected points

        Args
            tx (int) : x position
            ty (int) : y position
            radius (int) radius in squares
            char (char): character to draw
            color (curses color): mapped in util

        Returns
            pts affected (As calculated by fov.Ball
        '''
        pts = Global.pc.current_level.fov.Ball(tx, ty, radius, ignore_walls=False)
        for pt in pts:
            self.PutChar(pt[1], pt[0], "*", color)
        self.PutChar(ty,tx, "*", c_Red)
        animation_delay()     
        #self.pad.move(Global.pc.y, Global.pc.x)
        self.pad.refresh()
        for pt in pts:
            Global.pc.current_level.PaintSquare(pt[0], pt[1])
            #self.pad.move(Global.pc.y, Global.pc.x)
            #self.pad.refresh()
            self.move(Global.pc.y, Gobal.pc.x)
        return pts
    def Ask(self, question, opts, attr=c_yellow):
        "Ask the player a question."
        self.Message(question)
        while True:
            k = self.GetKey()
            if chr(k) in opts:
                answer = chr(k)
                break
        self.screen.addstr(0, 0, " " * self.width)
        self.messages_displayed = 0
        return answer
    def BeginTurn(self):
        "Called right after input is taken from the player."
        self.screen.addstr(0, 0, " " * self.width)
        self.screen.addstr(1, 0, " " * self.width)
        self.messages_displayed = 0
    def ClearScreen(self):
        self.screen.clear()
    def CreatureSymbol(self, mob):
        "Return a message code for a mob's symbol."
        tile = mob.tile
        color = "^0^"
        for k in msg_colors:
            if msg_colors[k] == mob.color:
                color = "^%s^" % k
        return "%s%s^0^" % (color, tile)
    def CommandList(self, pc, lattr=c_yellow, hattr=c_Yellow):
        "Display the keyboard commands to the player."
        L = []
        L.append("^Y^" + lang.label_movement_keys)
        L.append(" ^Y^7   8   9      y   k   u")
        L.append(" ^y^  \ | /          \ | /")
        L.append(" ^Y^4 ^y^- ^Y^5 ^y^- ^Y^6  ^y^%s  ^Y^h ^y^- ^Y^. ^y^- ^Y^l" % lang.word_or)
        L.append(" ^y^  / | \          / | \ ")
        L.append("^Y^ 1   2   3      b   j   n")
        L.append("^Y^5 ^y^%s ^Y^.^y^ %s" % (lang.word_or, lang.label_rest_one_turn))
        L.append(" ^Y^/^y^ %s" % lang.label_run)
        y = 2
        self.ClearScreen()
        self.addstr(0, 0, lang.label_help_title.center(self.width-1), self.stdscr,hattr)
        self.addstr(1, 5, lang.label_keyboard_commands, self.stdscr,hattr)
        special = {9: lang.key_tab}
        for c in pc.commands:
            keys = []
            for k in c.keys:
                try: keys.append(special[k])
                except KeyError: keys.append(chr(k))
            ckeys = (" ^0^%s^Y^ " % lang.word_or).join(keys)
            cstr = "^Y^%6s^y^ - %s" % (ckeys, c.desc[:32])
            if y < 22:
                self.addstr_color(y, 0, cstr, self.stdscr)
            else:
                self.addstr_color(11 + y - 22, 40, cstr, self.stdscr)
            y += 1
        for line in range(len(L)):
            self.screen.addstr_color(line+1, 44, L[line], c_yellow)
        self.addstr(self.height-1, 0, lang.prompt_any_key.center(self.width-1), self.stdscr,hattr)
        self.GetKey()
        self.ClearScreen()
        return
    def DetailedStats(self, pc):
        "Show a detailed player stats screen."
        self.screen.clear()
        L = []
        L.append(("^Y^-= %s =-" % lang.label_char_title) % (pc.name, pc.level, pc.archetype.cname))
        L.append("")
        b = pc.MeleeDamageBonus()
        if b >= 0:
            b = "+%s" % b
        L.append("^Y^%s: %2s^0^  %s %s" % (lang.stat_abbr_str.upper(), 
                                           pc.stats("str"), b, lang.label_melee_damage))
        L.append("         %.2fs carried, %s: %2s" % (pc.inventory.TotalWeight(), lang.stat_abbr_estr, pc.eSTR()))
        L.append("")
        b = pc.MeleeHitBonus()
        if b >= 0:
            b = "+%s" % b
        L.append("^Y^%s: %2s^0^  %s %s" % (lang.stat_abbr_dex.upper(), pc.stats("dex"), b, lang.label_to_hit))
        b = pc.EvasionBonus()
        if b >= 0:
            b = "+%s" % b
        if pc.stats("dex") - 8 > pc.eSTR():
            limit = "^R^ %s^0^" % lang.label_evasion_limited
        else:
            limit = ""
        L.append("         %s %s%s" % (b, lang.word_evasion, limit))
        L.append("")
        L.append("^Y^%s: %2s^0^  %s%% %s" % 
                 (lang.stat_abbr_int.upper(), pc.stats("int"), 
                  max(0, min(100, 25*(10-pc.stats("int")))), lang.label_spell_failure))
        L.append("         %s%% %s" % (max(0, min(100, 25*(8-pc.stats("int")))), lang.label_item_use_failure))
        L.append("")
        y = 0
        for line in L:
            self.addstr_color(y, 0, line, c_yellow, self.stdscr)
            y += 1
        self.addstr_color(y+1, 0, "^Y^%s" % lang.prompt_any_key, self.stdscr)
        self.GetKey()
        self.screen.clear()
    def DisplayInventory(self, mob, norefresh=False, equipped=False, types=""):
        "Display inventory."
        # TODO: remove norefresh
        self.ClearScreen()
        y = 0
        if equipped:
            title = lang.label_equipped_items
        else:
            title = lang.label_backpack_items
        hattr, lattr, sattr = c_Yellow, c_yellow, c_White
        if mob.inventory.Num() == 0:
            # No items in the inventory:
            if mob.is_pc:
                self.addstr(y, 0, lang.error_carrying_nothing, self.stdscr, hattr)
            else:
                self.addstr(y, 0, lang.error_mob_carrying_nothing, self.stdscr, hattr)
            return y+1
        if mob.is_pc:
            weight = lang.label_inventory_weight % (
                mob.inventory.TotalWeight(), mob.inventory.Capacity())
        else:
            weight = ""
        self.addstr(y, 0, "%s: %s" % (title, weight), self.stdscr, hattr)
        y += 1
        if types == "":
            display_types = pyro_items.types
        else:
            display_types = [t for t in pyro_items.types if t[1] in types]
        for type, symbol in display_types:
            itemlist = [i for i in mob.inventory.ItemsOfType(type)
                        if (equipped and i[0] in mob.equipped)
                        or (not equipped and i[0] not in mob.equipped)]
            if itemlist:
                self.addstr(y, 0, symbol, self.stdscr, sattr)
                self.addstr(y, 2, "%s:" % type, self.stdscr, hattr)
                y += 1
                for i, letter in itemlist:
                    if i.quantity > 1:
                        qtystr = "%sx " % i.quantity
                    else:
                        qtystr = ""
                    self.addstr_color(y, 4, "^Y^%s^0^: %s%s" % 
                                             (letter, qtystr, i.Name()), self.stdscr, lattr)
                    y += 1
        return y
    def DisplayText(self, text, attr=c_white):
        "Display multiline text (\n separated) and wait for a keypress."
        self.ClearScreen()
        text = "\n".join(wrap(text, self.width-2))
        y = self.addstr_color(0, 0, text, self.stdscr, attr)
        self.addstr_color(y+1, 0, lang.prompt_any_key, self.stdscr, c_Yellow)
        self.GetKey()
        self.ClearScreen()
    def DrawPathToTarget(self):
        if self.path_clear:
            color = c_green
        else:
            color = c_red
        for x, y in self.path[1:-1]:
            self.PutChar(y, x, "*", color)
            Global.pc.current_level.Dirty(x, y)
    def EndTurn(self):
        "Called right before input is taken from the player."
        # Put the cursor on the @:
        if self.tab_targeting and Global.pc.target:
            #self.pad.move(Global.pc.target.y, Global.pc.target.x)
            self.move(Global.pc.target.y, Global.pc.target.x)
        else:
            self.move(Global.pc.y, Global.pc.x)
    def GetChoice(self, item_list, prompt="Choose one: ", nohelp=False, nocancel=True):
        "Allow the player to choose from a list of options with descriptions."
        # item_list must be a list of objects with attributes 'name' and 'desc'.
        if nohelp:
            ex = ""
        else:
            ex = "?"
        if not nocancel:
            ex += " "
            prompt += " (%s) " % lang.label_space_to_cancel
        choice = None
        while True:
            r = self.Menu([r.name for r in item_list],
                question=prompt, attr=c_yellow, key_attr=c_Yellow,
                doublewide=True, extra_opts=ex)
            if r == ' ':
                choice = None
                break
            if r in letters:
                # An item was chosen:
                choice = item_list[letters.index(r)]
                break
            if r == "?":
                # Show a description:
                r = self.Menu([r.name for r in item_list],
                    question = lang.prompt_describe_which_item,
                    attr=c_yellow, key_attr=c_Yellow,
                    doublewide=True)
                if r in letters:
                    self.ClearScreen()
                    y = 0
                    for line in wrap(item_list[letters.index(r)].desc, self.width-1):
                        self.addstr(y, 0, line, c_yellow, self.stdscr)
                        y += 1
                    self.WaitPrompt(y, c_Yellow)
        self.screen.clear()
        if Global.pc and Global.pc.current_level:
            Global.pc.current_level.Display(Global.pc)
            self.ShowStatus()
        return choice
    def GetDirection(self):
        "Ask the player for a direction."
        self.addstr(0, 0, lang.prompt_which_direction, self.stdscr)
        while True:
            k = self.GetKey()
            if k in range(49, 58):
                dx, dy = offsets[k-49]
                r = k, dx, dy
                break
            elif k in arrow_offsets:
                dx, dy = arrow_offsets[k]
                r = k, dx, dy
                break
            elif chr(k) in vi_offsets:
                dx, dy = vi_offsets[chr(k)]
                r = k, dx, dy
                break
            elif k in [ SPC, ESC ]:
                r = None, None, None
                break
        self.addstr(0, 0, " " * self.width, self.stdscr)
        return r
    def GetDirectionOrTarget(self, caster, target_range=None):
        '''Return a direction or a target for targetting.

        Returns
             class TargettingCommand:
                mode      = 'x' # x = cancel, t = mob, d = direction
                direction = [0,0]
                target    = None
                path      = []
                blocked   = []
        '''
        self.screen.addstr(0, 0, lang.prompt_direction_or_target)
        cmd = TargettingCommand()
        while True:
            k = self.GetKey()
            if k in range(49, 58):
                dx, dy = offsets[k-49]
                path, blocked = range_direction_path(caster.x, caster.y, target_range, [dx,dy], Global.pc.current_level.BlocksPassage)
                cmd.type='d'
                cmd.direction=[dx,dy]
                cmd.path = path
                cmd.blocked = blocked
                break
            elif k in arrow_offsets:
                dx, dy = arrow_offsets[k]
                path, blocked = range_direction_path(caster.x, caster.y, target_range, [dx,dy], Global.pc.current_level.BlocksPassage)
                cmd.type='d'
                cmd.direction=[dx,dy]
                cmd.path = path
                cmd.blocked = blocked
                break
            elif chr(k) in vi_offsets:
                dx, dy = vi_offsets[chr(k)]
                path, blocked = range_direction_path(caster.x, caster.y, target_range, [dx,dy], Global.pc.current_level.BlocksPassage)
                cmd.type='d'
                cmd.direction=[dx,dy]
                cmd.path = path
                cmd.blocked = blocked
                break
            elif k in [ SPC, ESC ]:
                cmd.type = 'x'
                break
            elif chr(k) == 't':
                target, (path, blocked) = self.GetTarget(target_range = target_range) 
                if target:
                    cmd.type = 't'
                    cmd.target = target
                    cmd.path = path
                    cmd.blocked = blocked
                else:
                    cmd.type = 'x'
                break
        self.addstr(0, 0, " " * self.width, self.stdscr)
        return cmd
       
    def GetItemFromInventory(self, mob, prompt=None, equipped=False, types="", notoggle=False):
        "Ask the player to choose an item from inventory."
        # If notoggle is true, then the player can't move between equipped and backpack
        hattr, lattr, sattr = c_Yellow, c_yellow, c_White
        need_refresh = True
        while True:
            if mob.inventory.Num() == 0: 
                y = self.DisplayInventory(mob, norefresh=True)
                self.addstr(y, 0, lang.prompt_any_key, self.stdscr, hattr)
                item = None
                self.GetKey()
                break
            elif need_refresh:
                if prompt is None:
                    prompt = lang.prompt_choose_item
                if equipped:
                    other = lang.label_backpack_items.lower()
                else:
                    other = lang.label_equipped_items.lower()
                y = self.DisplayInventory(mob, norefresh=True, equipped=equipped, types=types)
                if notoggle:
                    toggle = ""
                else:
                    toggle = "'/' for %s, " % other
                pr = "%s (%s%s): " % (prompt, toggle, lang.label_space_to_cancel)
                self.screen.addstr(y, 0, pr, hattr)
                need_refresh = False
                # TODO: need_refresh is no longer meaningful
            k = self.GetKey()
            if k in [ SPC, ESC ]:
                item = None     # Cancelled by user; return None.
                break
            if k == 47 and not notoggle:    # "/"
                equipped = not equipped
                need_refresh = True
            try:
                item = mob.inventory.GetItemByLetter(chr(k))
                if item is None:
                    continue
                break
            except ValueError:
                continue
        self.ClearScreen()
        Global.pc.current_level.Display(Global.pc)
        self.ShowStatus()
        return item
    def GetKey(self):
        "Return the next keystroke in queue, blocking if none."
        self.screen.refresh()
        if Global.KeyBuffer:
            # Take the keystroke from the buffer if available
            # (for automated testing and maybe macros)
            k, Global.KeyBuffer = Global.KeyBuffer[0], Global.KeyBuffer[1:]
            return ord(k)
        k = 0
        while not 0 < k < 512:
            k = self.screen.getch()
            return k
    def GetLocation(self, prompt=lang.prompt_choose_location):
        "Ask the player to specify a square in the current level."
        x, y = Global.pc.x, Global.pc.y
        prompt = "%s (%s)" % (prompt, lang.prompt_enter_select_space_cancel)
        self.screen.addstr_color(0, 0, prompt, c_yellow)
        while True:
            self.move(y, x)
            k = self.GetKey()
            dx, dy = 0, 0
            if k in range(49, 58):
                dx, dy = offsets[k-49]
            elif chr(k) in vi_offsets:
                dx, dy = vi_offsets[chr(k)]
            elif k in [SPC,ESC]:
                r = None, None
                break
            elif k in (10, 13):
                r = x, y
                break
            x = max(0, min(x+dx, Global.pc.current_level.width-1))
            y = max(0, min(y+dy, Global.pc.current_level.height-1))
        self.addstr(0, 0, " " * self.width, self.stdscr)
        return r
    def GetMonsterChoice(self, prompt):
        monster = Global.IO.GetString(prompt,  noblank=True,
                                        pattr=c_yellow, iattr=c_Yellow)
        self.clearline(0, self.stdscr)
        return monster
    def GetQuantity(self, max_qty=None, prompt="How many?"):
        if max_qty:
            range = "1-%s, " % max_qty
        else:
            range = ""
        qstr = "[%s*=all, blank=cancel]" % range
        prompt = "%s %s: " % (prompt, qstr)
        qty = self.GetString(prompt, 0, 0, mask="0123456789*")
        self.clearline(0, self.stdscr)
        if qty == "*":
            return max_qty
        elif qty == "":
            return None
        else:
            try:
                qty = int(qty)
            except ValueError:
                self.Message(lang.error_bad_qty)
                return None
            if max_qty is not None:
                qty = min(qty, max_qty)
            return qty
    def GetSpell(self):
        "Ask the player to choose a spell."
        self.clearline(0, self.stdscr)
        spells = Global.pc.spells
        if not spells:
            self.Message(lang.error_no_spells_known)
            return None
        prompt = lang.prompt_choose_spell
        plen = clen(prompt)
        self.screen.addstr_color(0, 0, prompt)
        shortcut, spell = "", None
        while len(shortcut) < 3:
            k = chr(self.GetKey()).lower()
            if k in "abcdefghijklmnopqrstuvwxyz0123456789":
                shortcut += k
                self.addstr(0, plen + 1, shortcut.ljust(5), self.stdscr, c_Yellow)
                self.move(0, plen + len(shortcut) + 1, self.stdscr)
            elif k == ' ':
                self.clearline(0, self.stdscr)
                return None
            elif k in (chr(10), chr(13)):
                shortcut = Global.pc.last_spell
            elif k == '?':
                # Give the player a menu:
                all_spells = ["[%s] %s" % (s.shortcut, s.Name()) for s in spells]
                r = self.Menu(items=all_spells, doublewide=True, extra_opts = " ",
                              question = lang.prompt_choose_spell2)
                if r == " ":
                    return None
                else:
                    shortcut = spells[letters.index(r)].shortcut
        self.clearline(0, self.stdscr)
        try:
            spell = [s for s in spells if s.shortcut == shortcut][0]
        except IndexError:
            self.Message(lang.error_bad_spell_shortcut)
        Global.pc.last_spell = shortcut
        return spell
    def GetString(self, prompt, x=0, y=0, pattr=c_yellow, iattr=c_yellow,
                  max_length=999, noblank=False, nostrip=False, mask=None):
        "Prompt the user for a string and return it."
        mask = mask or " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
        str = ""
        self.addstr(y, x, prompt, self.stdscr, pattr)
        x += len(prompt)
        while True:
            self.screen.move(y, x + len(str))
            k = self.GetKey()
            if chr(k) in mask:
                str += chr(k)
            elif k == 8 or k == curses.KEY_BACKSPACE or k == DEL:
                # Backspace
                str = str[:-1]
            elif k in (10, 13):
                # Enter
                if str.strip() or not noblank:
                    if nostrip:
                        return str
                    else:
                        return str.strip()
            self.addstr(y, x, str+" ", self.stdscr, iattr)
    def GetTarget(self, prompt=lang.prompt_choose_target, LOS=True, target=None, target_range=None):
        """Ask the player to target a mob.

        Returns:
            mob : a creature selected for targetting
            (path, blocked) : list of Squares in the path,  list of blocked squres
        
        """
        path, clear = [], False
        mobs = self.NearbyMobCycler(target_range=target_range)
        if Global.pc.target:
            # If a target is already selected, default to it:
            x, y = Global.pc.target.x, Global.pc.target.y
            if not Global.pc.current_level.fov.Lit(x, y):
                x, y = Global.pc.x, Global.pc.y
            # If target not visible or out of range it can't be our target
            if target_range:
                range_to_target = calc_distance(Global.pc.x, Global.pc.y, Global.pc.target.x, Global.pc.target.y)
                if range_to_target > target_range:
                    x,y = Global.pc.x, Global.pc.y
        elif mobs:
            # If mobs are nearby, default to the closest one:
            mob, (path, clear) = mobs.next()
            x, y = mob.x, mob.y
        else:
            # Otherwise start at the player's location:
            x, y = Global.pc.x, Global.pc.y
        while True:
            mob = Global.pc.current_level.CreatureAt(x, y)
            if LOS:
                for i, j in path:
                    Global.pc.current_level.PaintSquare(i, j)
                path, clear = linear_path(Global.pc.x, Global.pc.y, x, y, Global.pc.current_level.BlocksPassage)
                if clear: color = c_green
                else: color = c_red
                if not Global.pc.current_level.fov.Lit(x, y):
                    path = []
                for i, j in path[1:]:
                    self.PutChar(j, i, "*", self.pad, color) 
                if mob:
                    # Repaint the last square if a mob is there, so the target
                    # path doesn't obscure it:
                    Global.pc.current_level.PaintSquare(*path[-1])
                if not path: mob = None
            if mob:
                if mob is Global.pc:
                    name = "^R^yourself^0^"
                else:
                    if clear:
                        blocked = ""
                    else:
                        blocked = " ^R^(%s)^0^" % lang.word_blocked
                    name = "^Y^%s^0^%s" % (mob.Name(), blocked)
            else:
                name = "nothing"
            prompt = lang.prompt_choose_target2 % name
            self.clearline(0, self.stdscr)
            self.addstr_color(0, 0, prompt, self.stdcr)
            self.move(y, x)
            k = self.GetKey()
            dx, dy = 0, 0
            if k in range(49, 58):
                dx, dy = offsets[k-49]
            elif chr(k) in vi_offsets:
                dx, dy = vi_offsets[chr(k)]
            elif k in [SPC,ESC]:
                # Space to cancel:
                mob = None
                for i, j in path:
                    Global.pc.current_level.PaintSquare(i, j)
                path = []
                break
            elif k == 9:
                # Tab to cycle targets:
                if mobs:
                    mob, (self.path, self.path_clear) = mobs.next()
                    x, y = mob.x, mob.y
            elif k in (10, 13):
                # Enter to select:
                # TODO: Allow targeting an empty square, maybe for certain spells only.
                if mob: break
            x = max(0, min(x+dx, Global.pc.current_level.width-1))
            y = max(0, min(y+dy, Global.pc.current_level.height-1))
        self.addstr(0, 0, " " * self.width, self.stdscr)
        self.addstr(1, 0, " " * self.width, self.stdscr)
        for i, j in path:
            Global.pc.current_level.PaintSquare(i, j)
        return mob, (path, clear)
    def Menu(self, items=[], x=0, y=0, doublewide=False, extra_opts="",
             prompt=lang.prompt_menu_default, question="", attr=c_yellow,
             key_attr=c_Yellow, prompt_attr=c_Yellow):
        "Display a list of options to the user and get their choice."
        if not items:
            raise ValueError("Empty option list")
        num = len(items)
        if num == 1:
            opts = ["a"]
        else:
            opts = ["a-%s" % letters[num-1]]
        opts.extend(extra_opts)
        disp_opts = []
        for o in opts:
            if o == ' ':
                disp_opts.append(lang.word_space)
            else:
                disp_opts.append(o)
        prompt = prompt.replace('$opts$', "[%s]" % ", ".join(disp_opts))
        self.ClearScreen()
        if question:
            self.addstr(y, x, question, self.stdscr, prompt_attr)
            y += 1
        max_y = 0
        for i in range(num):
            if doublewide:
                max_item_width = int((self.width - x) / 2 - 4)
                if i < num / 2 + num % 2:
                    # left side
                    X = x
                    Y = y+i
                else:
                    # right side
                    X = self.width / 2
                    Y = y + i - num / 2 - num % 2
            else:
                max_item_width = self.width - x - 4
                X = x
                Y = y + i
            self.addstr(int(Y), int(X), letters[i], self.stdscr, key_attr)
            self.addstr(int(Y), int(X)+1, " - %s" % items[i][:max_item_width], self.stdscr, attr)
            max_y = max(max_y, Y)
        self.screen.addstr(max_y+1, x, prompt, prompt_attr)
        while True:
            try:
                ch = chr(self.GetKey())
            except ValueError:
                continue
            if ch in letters[:num] + extra_opts:
                self.screen.clear()
                return ch
    def Message(self, msg, attr=c_yellow, nowait=False, forcewait=False):
        "Display a message to the player, wrapping and pausing if necessary."
        if not msg.strip():
            raise ValueError
        for m in wrap(msg, self.width - 7):
            self.ShowMessage(m, attr, nowait, forcewait)
            self.message_log.append((m, attr))
            self.message_log = self.message_log[-MESSAGE_LOG_SIZE:]
    def MessageLog(self):
        self.screen.clear()
        for i in range(1, min(len(self.message_log)+1, self.height)):
            msg, attr = self.message_log[-i]
            self.addstr_color(self.height - i - 1, 0, msg, self.stdscr, attr)
        self.addstr_color(self.height-1, 0, lang.prompt_any_key, self.stdscr, c_Yellow)
        self.GetKey()
        self.screen.clear()
    def MorePrompt(self):
        if self.messages_displayed > 1:
            self.addstr(1, self.width-7, lang.prompt_more, self.stdscr, c_Yellow)
            self.GetKey()
            self.messages_displayed = 0
            self.addstr(0, 0, " " * self.width, self.stdscr)
            self.addstr(1, 0, " " * self.width, self.stdscr)
    def NearbyMobCycler(self, target_range=None):
        "Return a Cycler instance for mobs near the PC."
        # Build a list of targetable mobs:
        nearby_mobs = [mob for mob in Global.pc.current_level.AllCreatures() if mob.pc_can_see ]
        if target_range:
            nearby_mobs = [mob for mob in nearby_mobs if calc_distance(Global.pc.x, Global.pc.y, mob.x, mob.y) <= target_range]
        if not nearby_mobs:
            return None
        targets = [(mob, linear_path(Global.pc.x, Global.pc.y, mob.x, mob.y,
                                     Global.pc.current_level.BlocksPassage))
                    for mob in nearby_mobs]
        # Sort by distance:
        targets.sort(key=lambda m: (m[0].x-Global.pc.x)**2 + (m[0].y-Global.pc.y)**2)
        return Cycler(targets)
    def PutTile(self, x, y, tile, color):
        self.PutChar(y, x, tile, color)
    def ShowMessage(self, msg, attr, nowait, forcewait):
        self.MorePrompt()
        self.addstr_color(self.messages_displayed, 0, msg, self.stdscr, attr)
        self.wait_x = clen(msg) + 1
        if nowait:
            self.screen.refresh()
        elif forcewait:
            self.messages_displayed = 2
            self.MorePrompt()
        else:
            self.messages_displayed += 1
    def ShowStatus(self):
        "Show key stats to the player."
        p = Global.pc
        exp_to_go = p.xp_for_next_level - p.xp
        if float(p.hp)/p.hp_max < 0.15:
            hp_col = "^R^"
        elif float(p.hp)/p.hp_max < 0.25:
            hp_col = "^Y^"
        else:
            hp_col = "^G^"
        if p.mp_max == 0 or float(p.mp)/p.mp_max < 0.2:
            mp_col = "^M^"
        else:
            mp_col = "^B^"
        stats = ("%s:%s(%s) %s:%s %s:%s %s:%s" % 
                 (lang.word_level_abbr.title(), p.level, exp_to_go, 
                  lang.stat_abbr_str.title(), p.stats("str"), 
                  lang.stat_abbr_dex.title(), p.stats("dex"), 
                  lang.stat_abbr_int.title(), p.stats("int")))
        hp = "%s%s:%s/%s^0^" % (hp_col, lang.word_hitpoints_abbr.upper(), p.hp, p.hp_max)
        if p.mp_max + p.mp > 0:
            mp = " %s%s:%s/%s^0^" % (mp_col, lang.word_mana_abbr.upper(), p.mp, p.mp_max)
        else:
            mp = ""
        if p.EvasionBonus() < p.RawEvasionBonus():
            ecolor = "^R^"
        else:
            ecolor = "^0^"
        armor = "%s:%s %s%s:%s^0^" % (lang.word_protection_abbr.title(), p.ProtectionBonus(), ecolor, 
                                      lang.word_evasion_abbr.title(), p.EvasionBonus())
        dlvl = "%s:%s" % (lang.word_dungeonlevel_abbr, p.current_level.depth)
        line = "%s  %s%s  %s  %s" % (stats, hp, mp, armor, dlvl)
        status_lines = []
        status_lines.append(line)
        #self.screen.addstr(MESSAGE_LINES+p.current_level.height, 0, " " * self.width)
        #self.screen.addstr_color(MESSAGE_LINES+p.current_level.height, 0, line)
        if Global.pc.target:
            target = Global.pc.target.Name().title()
            target_color = "^Y^"
        else:
            target = lang.word_none.title()
            target_color = "^0^"
        line = "%s: %s%s^0^" % (lang.word_target.title(), target_color, target)
        #self.screen.addstr(MESSAGE_LINES+p.current_level.height+1, 0, " " * self.width)
        #self.screen.addstr_color(MESSAGE_LINES+p.current_level.height+1, 0, line)        
        status_lines.append(line)
        self.set_status(status_lines)
    def Shutdown(self):
        "Shut down the IO system."
        # Restore the terminal settings:
        self.screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
    def TabTarget(self):
        "Allow the player to cycle through available targets."
        if not self.tab_targeting:
            self.target_mobs = self.NearbyMobCycler()
            if not self.target_mobs: return
            # Enter tab target mode:
            self.tab_targeting = True
            mob, (self.path, self.path_clear) = self.target_mobs.next()
        if self.path_clear:
            blocked = ""
        else:
            blocked = " ^R^(%s)^0^" % lang.word_blocked
        self.Message("%s: ^Y^%s%s" % (lang.label_now_targeting, mob.Name().title(), blocked))
        Global.pc.target = mob
    def WaitPrompt(self, y, attr=c_white, prompt=lang.prompt_any_key):
        self.addstr(y, 0, prompt, self.stdscr, attr)
        self.GetKey()
    def YesNo(self, question, attr=c_yellow):
        "Ask the player a yes or no question."
        self.MorePrompt()
        self.addstr(0, 0, " " * self.width, self.stdscr)
        self.addstr(0, 0, "%s [%s/%s]: " % 
                           (question, lang.word_yes_key, lang.word_no_key), self.stdscr, attr)
        yes_keys = lang.word_yes_key.upper() + lang.word_yes_key.lower()
        no_keys = lang.word_no_key.upper() + lang.word_no_key.lower()
        while True:
            k = chr(self.GetKey())
            if k in yes_keys:
                answer = True
                break
            elif k in no_keys:
                answer = False
                break
        self.addstr(0, 0, " " * self.width, self.stdscr)
        self.messages_displayed = 0
        return answer




    def set_status(self, lines):
        for idx, line in enumerate(lines):
            self.addstr_color(idx+1,1,' ' * len(line), self.status_win)
            self.addstr_color(idx+1,1,line, self.status_win)
        self.status_win.refresh()

    def addstr(self, y, x, s, win, attr=c_yellow):
        strs = s.split("\n")
        for s in strs:
            win.addstr(y, x, s, self.colors[attr])
            y += 1
        return y - 1

    def addstr_color(self, y, x, text, win,  attr=c_yellow):
        "addstr with embedded color code support."
        # Color codes are ^color^, for instance,
        # "This is ^R^red text^W^ and this is white."
        buff = ""
        base_attr = attr
        while text:
            ch, text = text[0], text[1:]
            if ch == "^":
                if text[:2] == "0^":
                    text = text[2:]
                    y = self.addstr(y, x, buff, win, attr)
                    x += len(buff)
                    buff, ch = "", ""
                    attr = base_attr
                    continue
                for color in msg_colors.keys():
                    code = "%s^" % color
                    if text[:2] == code:
                        text = text[2:]
                        y = self.addstr(y, x, buff, win, attr)
                        x += len(buff)
                        buff, ch = "", ""
                        attr = msg_colors[color]
                        break
                else:
                    buff += ch
            else:
                buff += ch
        if buff:
            y = self.addstr(y, x, buff, win, attr)
        return y


    '''
    def handle_input(self):
        while 1:
            key = self.stdscr.getch()
            if key == ord('q'):
                break
            elif key == ord('u'):
                self.ul_y = min(self.pad_height-self.game_height, self.ul_y+10)
                self.move(self.ul_x, self.ul_y)
            elif key == ord('d'):
                self.ul_y = max(0, self.ul_y-10)
                self.move(self.ul_x, self.ul_y)
            elif key == ord('r'):
                self.ul_x = min(self.pad_width-self.game_width, self.ul_x+10)
                self.move(self.ul_x, self.ul_y)
            elif key == ord('l'):
                self.ul_x = max(0, self.ul_x-10)
                self.move(self.ul_x, self.ul_y)
            elif key == ord('m'):

                submenu_items = [                                                    
                        ('beep', curses.beep),                                       
                        ('flash', curses.flash)                                      
                        ]                                                            
                submenu = Menu(submenu_items, stdscr)                           

                main_menu_items = [                                                  
                        ('beep', curses.beep),                                       
                        ('flash', curses.flash),                                     
                        ('submenu', submenu.display)                                 
                        ]                              
                main_menu = Menu(main_menu_items, self.stdscr)                       
                main_menu.display()

                # Redraw
                self.msg_win.touchwin()
                self.status_win.touchwin()
                self.stats_win.touchwin()
                self.stats_win.refresh()
                self.msg_win.refresh()
            lines = [ 'x = ^R^{0}, ^0^y = ^G^{1}'.format(self.ul_x,self.ul_y) ]
            self.set_status(lines)
        curses.doupdate()
        pad.touchwin()
    '''
    def clear(self):
        self.dattr = self.colors[0]
        self.chars = [[" "] * self.width for i in range(self.height)]
        self.attrs = [[self.colors[0]] * self.width for i in range(self.height)]
        self.cursor = [0, 0]
        self.pad.clear()
        self.pad.refresh(0,0,1,1,40,78)
        Global.FullDungeonRefresh = True
        for win in [ self.msg_win, self.status_win, self.stats_win ]:
            win.refresh()
    def clearline(self, lines, win):
        "Clear one or more lines."
        try:
            for line in lines:
                self.addstr(line, 0, ' ' * self.width, win, c_white)
        except TypeError:
            self.addstr(lines, 0, ' ' * self.width, win, c_white)
    def getch(self):
        return self.screen.getch()
    def keypad(self, arg):
        return self.screen.keypad(arg)
    def move(self, x, y):
        x,y = Global.pc.x, Global.pc.y
        x_step = self.game_width  // 2
        y_step = self.game_height // 2

        adj_x = max(x - self.game_width  // 2, 0)
        adj_y = max(y - self.game_height // 2, 0)
        
        if self.game_ul_x == -1 or self.game_ul_y == -1:
            # initial center
            y, x = adj_y, adj_x
            self.game_ul_x = x; self.game_ul_y = y
        else:
            if x - self.game_ul_x < 5: 
                self.game_ul_x = max(self.game_ul_x - x_step, 0)
            elif (self.game_ul_x+self.game_width) - x < 5:
                #try to move right
                self.game_ul_x = min(self.game_ul_x + x_step, self.pad_width-self.game_width)
            if y - self.game_ul_y < 5:
                # try to move up
                self.game_ul_y = max(self.game_ul_y - y_step, 0)
            elif (self.game_ul_y+self.game_height) - y < 5:
                # try to move down
                self.game_ul_y = min(self.game_ul_y + y_step, self.pad_height-self.game_height)
            
        
        self.pad.refresh(  self.game_ul_y, self.game_ul_x,
                           self.game_start_y, self.game_start_x,
                           self.game_start_y + self.game_height-2, 
                           self.game_start_x + self.game_width-2 )
        curses.doupdate()
        self.pad.touchwin()

    def PutChar(self, y, x, ch, attr):
        if True or self.chars[y][x] != ch or self.attrs[y][x] != attr:
            self.pad.addstr(y, x, ch, curses.color_pair(attr))                
    def refresh(self):
        self.pad.refresh(0,0,1,1,40,78)
        for win in [ self.msg_win, self.status_win, self.stats_win ]:
            win.refresh()

def main(stdscr):
    G = gui(stdscr)
    G.handle_input()

if __name__ == '__main__':
    wrapper(main)
