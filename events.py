"""
An Event is a timed thing that will happen on a future turn, but which is not
a dude.  This module governs the behavior of Events.

(1) An Event should have a currentLevel property, just like a Dude.
(2) An Event should have an act() function that governs what happens when
    it occurs, just like a dude.
"""

import action
import symbol
import coordinates
import kb
import config
import dude

class Event(object):
    """
    An Event is thing which will happen on a future turn, unattached to a dude.
    """
    
    def __init__(self, current_level):
        self.currentLevel = current_level
        self.existence = True

    def die(self):
        self.currentLevel.kill(self)
        self.existence = False
    
    def exists(self):
        return self.existence

    def isPlayer(self):
        return False

    def getType(self):
        return dude.qt.EVENT

class LevelTick(Event):
    """
    An Event which updates the status of a Level once per turn.

    Like a Dude, a LevelTick has an act() method; when this method is called,
    the LevelTick updates the state of its level.
    """

    def __init__(self, current_level):
        """
        Initialize a LevelTick for the level provided.

        current_level - the Level which the LevelTick should update if its act()
            method is called.
        """
        Event.__init__(self, current_level)
        return

    def act(self):
        """
        Update the state of the LevelTick's level.  Return True.
        """
        self.currentLevel.player.deck.draw()
        return config.TURN_TICKS

class SummoningEvent(Event):
    """
    An event which creates enemies when all enemies on the field are dead.
    """

    def __init__(self, currentLevel):
        Event.__init__(self, currentLevel)
        self.summons_so_far = 0

    def act(self):
        """
        Check if all enemies are dead. If so, summon new ones.
        """
        
        for d in self.currentLevel.dudeLayer:
            if not d.isPlayer():
                return config.TURN_TICKS

        action.Summon(self.currentLevel, self.summons_so_far).do()
        self.summons_so_far += 1

        return config.TURN_TICKS

def isEventAtCoords(event_class, coords, level_):
    """
    Return whether there is an Event of a certain type scheduled to occur at a
    certain location.

    event_class - the class of Event which is being looked for.  This Event
        should have a coords field.
    coords - the coordinates being searched.
    level_ - the level on which the events are being held.

    Return - true if there is an Event of class event_class at the coordinates
        specified; false otherwise.
    """

    for event in level_.events:
        if isinstance(event, event_class) and event.coords == coords:
            return True

    return False
