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

import coordinates
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
    """
    Fields:
    source - the Dude moving.
    coords - the relative coordinates to which the Dude is moving.  For
        instance, if coords = (1, 0) and source is at (2, 2), it will move
        to (3, 2).
    """
    
    def __init__(self, source, coords):
        """
        Coords should be the relative coords of the destination to the source.
        """
        
        Action.__init__(self, "MOVE")
        self.source = source
        self.coords = coords
    
    def getCoords(self):
        return self.coords

    def do(self):
        """
        Move the source of the action in the direction specified.
        Raise a ValueError if such a move is illegal.
        
        act - the action to be performed.

        Returns True if the move can be performed, and returns False if it
        cannot.
        """
        destination_coords = coordinates.add(self.source.coords, self.coords)

        if self.source.canMove(destination_coords):
            self.source.currentLevel.moveDude(self.source, destination_coords)
            return True
        else:
            return False
#            raise ValueError("This dude, %s, at %s, cannot move to %s." %
#                (str(self.source),
#                 str(self.source.coords),
#                 str(destination_coords)))

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

    Fields:
    source - the Dude waiting.
    """
    
    def __init__(self, source):
        Action.__init__(self, "WAIT")

        self.source = source

    def do(self):
        """
        Do nothing, and return True.
        """

        return True

class Attack(Action):
    """
    An action that represents attacking another dude.

    Instance fields:
    source - the dude attacking.
    target - the dude getting attacked.
    """
    
    def __init__(self, source, target, message = "%(SOURCE_NAME)s attacks %(TARGET_NAME)s! (%(DAMAGE)d)"):
        Action.__init__(self, "STDATK", message)
        self.source = source
        self.target = target

    def do(self):
        """
        Have the source of the action attack its target.

        act - the action to be performed.

        Returns True.
        """
        damage_dealt = damage(self.source.attack, self.target.defense,
                       self.source.char_level, self.target.char_level)
        self.source.currentLevel.messages.append(self.message % {
            "SOURCE_NAME": self.source.getName(),
            "DAMAGE": damage_dealt,
            "TARGET_NAME": self.target.getName(),
            })
        self.target.cur_HP -= damage_dealt
        self.target.checkDeath()

        return True

def is_generic_action(act):
    """
    Return True if the action passed is a generic action both lots of players
    and lots of monsters could be expected to do.

    Currently, the following actions are considered generic:
    - Attack
    - Move
    - Wait
    """

    code = act.getCode()
    if code in ("STDATK", "MOVE", "WAIT"):
        return True
    else:
        return False

def do_generic_action(act):
    """
    Perform the generic action passed.  Return True if this action takes up
    a turn.  (Currently, this will always be the case.)

    act - the action to be performed.

    Raises a ValueError if is_generic_action(act) is false.
    """

    if not is_generic_action(act):
        raise ValueError("The act, %s, is not a generic action." % str(act))

    return act.do()

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
