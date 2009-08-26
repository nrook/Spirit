"""
Creates and manages "special effects" to be used on the screen.
"""

import collections

import tcod_display as display
import threading
import config
import arrays
import exc

BLINKING_TIME = 0.7

thr = None
ev = None

def init():
    """
    Initialize the thread responsible for animating effects.
    """

    global thr
    global ev

    ev = threading.Event()
    thr = threading.Thread(target=repeat, args=(ev, BLINKING_TIME, animate))
    thr.start()

def repeat(event):
    while True:
        event.wait(BLINKING_TIME)
        if event.isSet():
            break
        # do animation things

def stop():
    ev.set()

class EffectsMap(object):
    """
    A container which represents special effects over a Level.
    
    Fields:
    dimensions - the dimensions of the effectsMap and, thus, the level.
    """
    """
    __map - the actual map of lists which contains this effectsMap.
    """

    def __init__(self, dimensions):
        self.dimensions = dimensions
        self.__map = dict()

    def add(self, coords, glyph):
        """
        Add a given glyph to the top of the map at given coordinates.

        coords - the coordinates at which the glyph should be added.
        glyph - the glyph to be displayed.
        """
        exc.check_in_array(coords, self.dimensions)

        if coords in self.__map:
            self.__map[coords].insert(0, glyph)
        else:
            self.__map[coords] = [glyph]

    def remove(self, coords, glyph = None):
        """
        Remove a given glyph from the map.

        If glyph = None, then the top glyph is removed from the
        given coordinates.

        coords - the coordinates from which the glyph should be removed.
        glyph - the glyph to remove.  If this glyph shows up multiple times
            in the square, it is only removed once (at its highest point).

        Returns the glyph removed.  Will raise a KeyError if there is no glyph
        at the coordinates requested, or a ValueError if the specific glyph
        is not present at these coordinates.
        """

        if coords not in self.__map:
            raise KeyError("There is no glyph at the coordinates %s." % coords)

        if glyph is None:
            ret_glyph = self.__map[coords].pop(0)
            if len(self.__map[coords]) == 0:
                del self.__map[coords]
            return ret_glyph
        else:
            try:
                self.__map[coords].remove(glyph)
            except ValueError:
                raise ValueError("The glyph %s is not present at %s." % (glyph, coords))
            else:
                if len(self.__map[coords]) == 0:
                    del self.__map[coords]
                return glyph

    def getArray(self):
        """
        Return an array representing this object's contents.
        """

        ret_array = arrays.empty_str_array(self.dimensions)
        for i in self.__map:
            ret_array[i] == self.__map[i][0]
        return ret_array

    def get(self, coords):
        """
        Return the top glyph, the one that should be displayed, at coords.
        """
        
        if coords in self.__map:
            return self.__map[coords][0]
        else:
            return config.TRANSPARENT_GLYPH
