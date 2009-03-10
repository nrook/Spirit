"""
The goals of display.py are to give a platform-independent method
of storing the data being shown on the console on-screen.  A
Window will consist of a number of objects, each of which has a
Panel() method which returns an array, and a DiffPanel method which
returns a list of "hot" squares on this Panel.
"""

import numpy

class Window(object):
    """An object representing the view of the screen, containing a
    number of arrays (or objects with arrays in them)."""

    def __init__(self, dimensions = (80, 24), dudes = None, items = None,
        elems = None, terrain = None):
        """Create a Window made up of four supplied objects which supply
        arrays."""

        if dudes = None
