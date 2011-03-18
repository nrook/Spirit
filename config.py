"""
Contains a bunch of constants and program-wide values.
"""

WIZARD = False

DEFAULT_MAP_X_WIDTH = 80 #Default width of the entire screen
DEFAULT_MAP_Y_WIDTH = 24 #Default height of the entire screen

DEFAULT_DIMENSIONS = (DEFAULT_MAP_X_WIDTH, DEFAULT_MAP_Y_WIDTH)

MAP_DIMENSIONS = (60, 17)
MESSAGES_DIMENSIONS = (80, 7)
STATUS_DIMENSIONS = (20, 17)  #column 1 intentionally left blank

TURN_TICKS = 72

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

RUN_DIRECTION_SWITCH = {
                       kp.RNW: (-1, -1),
                       kp.RW: (-1, 0),
                       kp.RSW: (-1, 1),
                       kp.RS: (0, 1),
                       kp.RSE: (1, 1),
                       kp.RE: (1, 0),
                       kp.RNE: (1, -1),
                       kp.RN: (0, -1)}

import symbol

TRANSPARENT_GLYPH = symbol.Glyph(' ', (0, 0, 0))

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


