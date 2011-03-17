"""
Contains the basic FixedObject class, from which all other locational classes

are derived.
"""

import symbol
import objid
import config

class FixedObject(object):
    """
    A fixed object - that is, an object with coordinates in space
    
    Each fixed object must also have a 'glyph', a symbol or tile that reps it.
    Each fixed object also has a unique ID.
    """
    
    def __init__(self, coords, glyph = symbol.BAD_GLYPH, currentLevel = None):
        object.__init__(self)
        self.ID = config.getID()
        self.coords = coords
        self.glyph = glyph
        self.currentLevel = currentLevel
    
    def __str__(self):
        return "%s (%s): %s" % (self.glyph, self.getID(), self.getCoords())
    
    def move(self, newCoords):
        self.coords = newCoords
    
    def getID(self):
        return self.ID
    
    def getCoords(self):
        return self.coords
    
    def setCoords(self, coords):
        self.coords = coords
    
    def getCurrentLevel(self):
        return self.currentLevel
    
    def setCurrentLevel(self, currentLevel):
        self.currentLevel = currentLevel

    def getCurGlyph(self):
        return self.glyph
