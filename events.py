"""
An Event is a timed thing that will happen on a future turn, but which is not
a dude.  This module governs the behavior of Events.

(1) An Event should have a currentLevel property, just like a Dude.
(2) An Event should have an act() function that governs what happens when
    it occurs, just like a dude.
"""

import action
import symbol

class Event(object):
    """
    An Event is thing which will happen on a future turn, unattached to a dude.
    """
    
    def __init__(self, current_level):
        self.currentLevel = current_level

    def die(self):
        self.currentLevel.events.remove(self)

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

        self.currentLevel = current_level
        
        return

    def act(self):
        """
        Update the state of the LevelTick's level.  Return True.
        """
        
        self.currentLevel.player.deck.draw()
        self.currentLevel.player.regenerate()
        return True

class TimedExplosion(Event):
    """
    An Event which will set off an Explode action in a certain number of rounds.
    """
    
    EXPLOSION_GLYPH = symbol.Glyph('o', (65, 255, 0))

    def __init__(self, currentLevel, coords, damage, time):
        """
        Create a TimedExplosion for the future.

        currentLevel - the Level on which the explosion should occur.
        coords - the coordinates on which the explosion should occur.
        damage - the damage which the explosion should do.
        time - the number of rounds which must pass before the explosion goes
            off.  0 means the explosion occurs at the end of the turn, 1 at the
            end of next turn, etc.
        """

        Event.__init__(self, currentLevel)
        self.explode_action = action.Explode(currentLevel, coords, damage)
        self.time = time
        self.coords = coords
        currentLevel.addSolidEffect(self.EXPLOSION_GLYPH, coords)

    def act(self):
        """
        Update the TimedExplosion, decrementing the timer and exploding if
        time is up.
        """

        if self.time == 0:
            # Explode.
            self.currentLevel.messages.append("The grenade goes off!")
            self.explode_action.do()
            self.currentLevel.removeSolidEffect(self.coords)
            self.die()
        else:
            self.time -= 1

        return True

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

def is_grenade_at_coords(coords, level_):
    return isEventAtCoords(TimedExplosion, coords, level_)
