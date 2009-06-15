"""
Defines a central Action class, which includes any in-game actions dudes take.

Also included are sub-classes for specific Actions.  Note that no Actions
include code to actually perform themselves; they are strictly data.  The
Action module also includes various formulas, such as the damage dealt by an
attack or the HP gained on gaining a level.
"""

"""
Codes:

Quit (unused): QUIT
Move: MOVE
Stand still: WAIT
Standard attack: STDATK
Special melee attack: SPMELEE
Explode: EXPLODE
Go upstairs: UP
"""

"""
Spec codes are codes for special attacks or actions used by the player or a
monster.  Most monsters have a spec code representing the single type of
special attack they can use.

Spec codes:
Melee attacks:
CRITICAL: Perform a critical hit, with a CRIT_MULTIPLIER damage multiplier.
"""

import coordinates
import rng
import events
import tcod_display as display
import exc

CRIT_MULTIPLIER = 2
KNOCK_DAMAGE = 5
KNOCK_DISTANCE = 10

class Action(object):
    """
    An object representing an action a dude could take.
    Also includes a do() method, which actually does said action.

    Fields:
    strcode - a code representing the Action's type.  Use getCode() instead.
    message - a string representing a message to be displayed when the Action
        is taken.
    """
    
    def __init__(self, strcode, message = ""):
        """
        strcode is a code representing the type of action.
        
        As no generic Actions should exist, it should only be called by
        subclasses of Action.
        """
        
        self.strcode = strcode
        self.message = message
    
    def getCode(self):
        return self.strcode

class DoNothing(Action):
    """
    An object representing a dude not taking an action, not even using a turn.

    Fields:
    strcode - "DO NOTHING".
    """

    def __init__(self):
        Action.__init__(self, "DO NOTHING")

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

class SpecialMelee(Action):
    """
    An action that represents attacking an adjacent dude with a special
    ability.
    
    Instance fields:
    source - the dude attacking.
    target - the dude being attacked.
    code - a special code representing the type of special attack.
    """

    def __init__(self, source, target, code, message = "%(SOURCE_NAME)s uses a special attack on %(TARGET_NAME)s! (%(DAMAGE)d)"):
        Action.__init__(self, "SPMELEE", message)
        self.source = source
        self.target = target
        self.code = code

    def do(self):
        do_special_melee(self.code, self.source, self.target)
        return True

class Explode(Action):
    """
    An action representing an attack on a square and its adjacent squares.

    Explosions are fixed-damage.
    """

    def __init__(self, level_, coords, damage):
        Action.__init__(self, "EXPLODE", None)
        self.level_ = level_
        self.coords = coords
        self.damage = damage

    def do(self):
        for explosion_coords in coordinates.radius(1, self.coords, self.level_.dimensions):
            if explosion_coords in self.level_.dudeLayer:
                target = self.level_.dudeLayer[explosion_coords]
                target.cur_HP -= self.damage
                self.level_.messages.append("%s is hurt by the explosion! (%d)" %
                    (target.getName(), self.damage))
                target.checkDeath()

        return True

class ThrowGrenade(Action):
    """
    An action representing a grenade hurled short-range to a specific square.
    """

    def __init__(self, source, target_coords, damage):
        Action.__init__(self, "GRENTHROW", "%(SOURCE_NAME)s threw a grenade!")
        self.source = source
        self.target_coords = target_coords
        self.damage = damage

    def do(self):
        self.source.currentLevel.messages.append(self.message
            % {"SOURCE_NAME": self.source.getName()})
        self.source.currentLevel.events.append(events.TimedExplosion(self.source.currentLevel, self.target_coords, self.damage, 2))

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

def do_special_melee(attack_type, source, target):
    """
    Have a Dude perform a special melee attack.

    attack_type - a string representing the type of special attack.
    source - the Dude attacking.
    target - the Dude being attacked.
    """

    if attack_type == "CRITICAL":
        damage_dealt = CRIT_MULTIPLIER * \
                       damage(source.attack, target.defense,
                              source.char_level, target.char_level)
        source.currentLevel.messages.append(
        "%(SOURCE_NAME)s runs %(TARGET_NAME)s all the way through! (%(DAMAGE)d)"
            % {"SOURCE_NAME": source.getName(),
               "DAMAGE": damage_dealt,
               "TARGET_NAME": target.getName()})
        target.cur_HP -= damage_dealt
        target.checkDeath()
    elif attack_type == "KNOCK":
        damage_dealt = KNOCK_DAMAGE
        direction = coordinates.subtract(target.coords, source.coords)
        source.currentLevel.messages.append(
        "%(SOURCE_NAME)s delivers a wicked punch to %(TARGET_NAME)s! (%(DAMAGE)d)"
            % {"SOURCE_NAME": source.getName(),
               "DAMAGE": damage_dealt,
               "TARGET_NAME": target.getName()})
        for i in range(KNOCK_DISTANCE):
            display.refresh_screen()
            destination = coordinates.add(target.coords, direction)
            if target.canMove(destination):
                target.currentLevel.moveDude(target, destination)
            else:
                break
        display.refresh_screen()
        target.cur_HP -= damage_dealt
        target.checkDeath()
    elif attack_type == "EXPLODE":
        explode_action = Explode(source.currentLevel, source.coords, 10)
        source.currentLevel.messages.append(
        "%(SOURCE_NAME)s explodes!"
            % {"SOURCE_NAME": source.getName()})
        explode_action.do()
    else:
        raise exc.InvalidDataWarning("%s special ability used by %s on %s."
                                     % (attack_type, str(source), str(target)))

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
