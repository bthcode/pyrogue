"""
Pyro: PYthon ROguelike by Eric D. Burgess, 2006
"""


# Pyro modules:
from util import *

import creatures
import items
import player
import dungeons
import io_curses as io

import os
import sys
import argparse
import pickle


####################### CLASS DEFINITIONS #######################

class Pyro(object):
    "Main class in charge of running the game."
    def __init__(self):
        # Start a new game:
        self.game = Game()
    def Run(self):
        Global.IO.ClearScreen()
        try:
            while True:
                self.game.Update()
        except GameOver:
            #Global.IO.DisplayText("Goodbye.", c_yellow)
            log("Game ended normally.")
    def Save(self, savefile):
        Global.IO.DisplayText("Saving to file {0}".format(savefile))
        pickle.dump(self, open(savefile, 'wb'))
        
        
class Game(object):
    "Holds all game data; pickling this should be sufficient to save the game."
    def __init__(self):
        # Create the dungeon and the first level:
        self.dungeon = dungeons.Dungeon("Dingy Dungeon")
        self.current_level = self.dungeon.GetLevel(1)
        # Make the player character:
        self.pc = player.PlayerCharacter()
        # Put the PC on the up stairs:
        x, y = self.current_level.stairs_up
        self.current_level.AddCreature(self.pc, x, y)
    def Update(self):
        "Execute a single game turn."
        self.current_level.Update()
        
############################ MAIN ###############################

def StartGame():
    # Initialize the IO wrapper:
    Global.IO = io.IOWrapper()
    try:
        # Fire it up:
        Global.pyro = Pyro()
        Global.pyro.Run()
    finally:
        Global.IO.Shutdown()

def LoadGame(savefile):
    try:
        p = pickle.load(open(savefile, 'rb'))
    except pickle.UnpicklingError:
        print ("ERROR: Can't understand savefile: {0}".format(savefile))
        sys.exit(1)

    Global.IO = io.IOWrapper()
    try:
        Global.pyro = p
        Global.pc   = p.game.pc
        Global.pyro.Run()
    finally:
        Global.IO.Shutdown() 
# end LoadGame

if __name__ == "__main__":
    parser = argparse.ArgumentParser('')
    parser.add_argument('-s', '--savefile', type=str)
    args = parser.parse_args()
    if args.savefile:
        if not os.path.exists(args.savefile):
            print ("ERROR: Can't find savefile: {0}".format(args.savefile))
            sys.exit(1)
        LoadGame(args.savefile)
    else:
        StartGame()
