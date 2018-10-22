"""
Pyro: PYthon ROguelike by Eric D. Burgess, 2006
"""


# Pyro modules:
from util import *
from curses import wrapper

import creatures
import pyro_items 
import player
import dungeons
import io_curses as io

import os
import sys
import argparse
import pickle


####################### CLASS DEFINITIONS #######################

class Pyro(object):
    """
    Main class in charge of running the game.

    Attributes
    ----------
    game: An instance of :class:`Game`


    """
    def __init__(self):
        '''Start a new game.
        '''
        self.game = Game()

    def Run(self):
        '''
        Main while loop running the game 
        '''
        Global.IO.ClearScreen()
        try:
            while True:
                self.game.Update()
        except GameOver:
            log("Game ended normally.")

    def Save(self, savefile):
        '''
        Saves to a pickle file

        Args: 
            savefile (str): file to save to

        Returns:    
            None
        '''

        Global.IO.DisplayText("Saving to file {0}".format(savefile))
        pickle.dump(self, open(savefile, 'wb'))
        
        
class Game(object):
    '''Holds all game data
    
    Attributes:
        dungeon: An instance of :class:`pyrogue.dungeons.Dungeon`
        current_level: An instance of :class:`pyrogue.dungeons.Level`
        pc: An instance of :class:`pyrogue.player.PlayerCharacter`

    '''
    
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

def StartGame(stdscr):
    ''' Start a new game
    '''
    # Initialize the IO wrapper:
    Global.IO = io.IOWrapper(stdscr)
    try:
        # Fire it up:
        Global.pyro = Pyro()
        Global.pyro.Run()
    finally:
        Global.IO.Shutdown()

def LoadGame(savefile):
    ''' Load a game from a pickle file
    '''
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
        wrapper(LoadGame(args.savefile))
    else:
        wrapper(StartGame)
