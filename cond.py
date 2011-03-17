"""
Governs 'conditions', status effects that modify a Dude's movement in some way.
"""

import action
import coordinates
import symbol
import log

HASTE_COLOR = (0, 255, 255)

class Condition(object):
    """
    A condition.
    """

    def __init__(self, time, name):
        """
        Create a new Condition.

        time - the number of turns until the condition will wear off.
        name - a unique identifier for the condition, and the way it will be
               displayed to the player.
        """
        self.time = time
        self.name = name

    def getDisplayName(self):
        """
        Get the name of this condition used to display it on the Sidebar.

        If a condition does not want to be displayed on the Sidebar, this method
        should return an empty string.
        """
        return self.name

    def passTurn(self):
        """
        Indicate to the condition that a turn has passed.
        """
        self.time -= 1

    def isOver(self):
        """
        Return True if the condition is over, False otherwise.
        """
        return self.time < 0

    def getAction(self, dude_):
        """
        Get an action, if this condition decides to control its dude's actions.
        
        Returns "None" if the condition allows the dude to choose its own
        actions.
        """
        return None

    def modifyAction(self, act):
        """
        Modify an action, if that action is not allowed under this condition.

        Returns: the new action that will be performed in place of the old.
        """
        return act

    def modifyGlyph(self, glyph):
        """
        Modify the glyph of a dude to be displayed.

        Returns: the new glyph which should be displayed.
        """

        return glyph

    def apply(self, dude_):
        """
        Apply any effects that occur when the condition is given to a dude.
        """
        return

    def cancel(self, dude_):
        """
        Do any effects that occur once the condition is over.  That is, return
        the dude to its original state.
        """
        return

class Stuck(Condition):
    """
    A condition in which a dude cannot move.
    """
    
    def __init__(self, duration):
        Condition.__init__(self, 8, "stuck")

    def modifyAction(self, act):
        """
        If a dude is Stuck, all of their moves become Wait actions.
        """
        if act.strcode == "MOVE":
            return action.Wait(act.source)
        else:
            return act

class Haste(Condition):
    """
    A condition in which the dude's speed doubles.
    """

    def __init__(self, duration):
        Condition.__init__(self, duration, "haste")

    def modifyGlyph(self, glyph):
        """
        Turn the hasted thing a funny color to indicate its haste.
        """

        return symbol.Glyph(glyph.char, HASTE_COLOR)

    def apply(self, dude_):
        dude_.speed /= 2

    def cancel(self, dude_):
        dude_.speed *= 2

class TimeBomb(Condition):
    """
    A condition in which a dude explodes after a certain number of turns.
    """
    GRENADE_COLORS = {3 : (0, 255, 0),
                      2 : (0, 255, 0),
                      1 : (255, 255, 0),
                      0 : (255, 65, 0)}
    EXPLOSION_GLYPH = symbol.Glyph('#', (255, 0, 0))
    def __init__(self, timer):
        Condition.__init__(self, 0, "timebomb")
        self.timer = timer
        self.exploded = False

    def modifyGlyph(self, glyph):
        return symbol.Glyph(glyph.char, self.GRENADE_COLORS[self.timer])

    def passTurn(self):
        pass

    def isOver(self):
        return self.exploded

    def getAction(self, dude_):
        assert self.timer >= 0
        if self.timer == 0:
            return action.Detonate(dude_)
        else:
            return action.BombTick(dude_)

class Resting(Condition):
    """
    A condition in which a dude rests until it has full health.

    This condition is interrupted if there is a monster in sight.
    """

    def __init__(self):
        Condition.__init__(self, 200, "resting")

    def getDisplayName(self):
        return ""

    def getAction(self, dude_):
        if len(dude_.fov.dudes) > 0 or dude_.cur_HP >= dude_.max_HP:
            self.time = -5
            return None
        else:
            return action.Wait(dude_)

class Running(Condition):
    """
    A condition in which the player moves in a specific direction.

    This condition is interrupted if there is a monster in sight, or if there
    is something blocking the player's path.
    """

    def __init__(self, direction):
        Condition.__init__(self, 200, "running")
        self.direction = direction

    def getDisplayName(self):
        return ""

    def getAction(self, dude_):
        if dude_.canMove(coordinates.add(dude_.coords, self.direction)) \
            and len(dude_.fov.dudes) == 0:

            return action.Move(dude_, self.direction)
        else:
            self.time = -5
            return None
