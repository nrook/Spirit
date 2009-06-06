"""
Contains a bunch of constants and program-wide values.
"""

DEFAULT_MAP_X_WIDTH = 80 #Default width of the entire screen
DEFAULT_MAP_Y_WIDTH = 24 #Default height of the entire screen

DEFAULT_DIMENSIONS = (DEFAULT_MAP_X_WIDTH, DEFAULT_MAP_Y_WIDTH)

MAP_DIMENSIONS = (60, 17)
MESSAGES_DIMENSIONS = (80, 7)
STATUS_DIMENSIONS = (20, 17)  #column 1 intentionally left blank

from kb import kp

DIRECTION_SWITCH =  {
                    kp.NW: (-1, -1),
                    kp.W: (-1, 0),
                    kp.SW: (-1, 1),
                    kp.S: (0, 1),
                    kp.SE: (1, 1),
                    kp.E: (1, 0),
                    kp.NE: (1, -1),
                    kp.N: (0, -1)}

import symbol

TRANSPARENT_GLYPH = symbol.Glyph(' ', (0, 0, 0))

# Those symbols which represent the interior of a room, spaces which can be
# easily seen through.
# Put this in level instead!
# OPEN_GLYPHS = set(['.'])

# Those symbols which represent a square which is not easily seen through, but
# which is somewhat transparent (like cooridor spaces).
# Put this in level instead!
# SEMI_OPEN_GLYPHS = set(['#'])

import objid

class MapVars:
    def __init__(self, mapDims):
        self.dimensions = mapDims

mv = MapVars((DEFAULT_MAP_X_WIDTH, DEFAULT_MAP_Y_WIDTH))

def getID():
    """
    Returns an ID, guaranteed to be unique.
    """
    return IDFactory.get()

IDFactory = objid.ObjectIDFactory()

from dude import MonsterFactory

def getMonsterFactory():
    """
    Returns the primary monster factory.
    """
    return monFactory

monFactory = MonsterFactory()


