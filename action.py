"""
Defines a central Action class, which includes any in-game actions dudes take.

Also included are sub-classes for specific Actions.  Note that no Actions
include code to actually perform themselves; they are strictly data.  The
Action module also includes various formulas, such as the damage dealt by an
attack or the HP gained on gaining a level.
"""

"""
Codes:

Move: MOVE
Stand still: WAIT
Standard attack: STDATK
Go upstairs: UP
"""

import rng

class Action(object):
    
    def __init__(self, strcode, message = ""):
        """
        strcode is a code representing the type of action.
        
        As no generic Actions should exist, it should only be called by
        subclasses of Action.
        """
        
        #instance variables: strcode, message
        #if the Action displays no message, then message = ""
        
        self.strcode = strcode
        self.message = message
    
    def getCode(self):
        return self.strcode

class Move(Action):
    
    def __init__(self, coords):
        """
        Coords should be the relative coords of the destination to the source.
        """
        
        Action.__init__(self, "MOVE")
        self.coords = coords
    
    def getCoords(self):
        return self.coords

class Up(Action):
    """
    An action representing an attempt to move up a level.
    """
    def __init__(self):
        Action.__init__(self, "UP")
    

class Quit(Action):
    """
    An action that represents the player's desire to quit the game.
    """
    
    def __init__(self):
        Action.__init__(self, "QUIT")

class Wait(Action):
    """
    An action that represents staying in place.
    """
    
    def __init__(self):
        Action.__init__(self, "WAIT")

class Attack(Action):
    """
    An action that represents attacking another dude.
    """
    
    def __init__(self, target, message = "%(SOURCE_NAME)s attacks %(TARGET_NAME)s! (%(DAMAGE)d)"):
        
        #Instance variables: target (the dude who is being attacked)
        Action.__init__(self, "STDATK", message)
        self.target = target


def expected_HP(dude_level):
        return 6 * (dude_level + 2)

def HP_on_level_gain():
    """Determines what maximum HP increase the player gets on level gain.
    
    Currently, this HP boost should be between 3 and 9, and should
    most commonly be 6."""
    
    return rng.XdY(3, 3)

def damage(attack_power, defense_modifier, attacker_level, defender_level):
        expected_damage = float(attack_power) / 100
        defense_modifier = float(defense_modifier) / 100
        level_modifier = 2 ** ((attacker_level - defender_level) / 11.0)
        return int(expected_HP(attacker_level) * expected_damage *
            defense_modifier * level_modifier)
