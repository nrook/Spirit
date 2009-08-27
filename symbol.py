"""
'symbol' handles tiles and such.

Right now, it's pretty boring, as symbols that represent characters are just
one-element strings.
"""

import collections
import config
import arrays

REMEMBERED_COLOR = (99, 99, 99)

class Glyph(object):
    """
    The symbol that represents a character.
    """

    def __init__(self, char, color):
        """
        char - the character of the glyph.
        color - the color of the glyph, a 3-tuple of 0 to 255 ints.
        """

        self.char = char
        self.color = color
        self.r = color[0]
        self.g = color[1]
        self.b = color[2]

    def __eq__(self, other):
        return (self.char == other.char) and (self.color == other.color)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.char, self.color))

    def __str__(self):
        return self.char

BAD_GLYPH = ('!', 255, 0, 0)

class glyphMap(dict):
    """
    A map which returns the transparent glyph on a lookup failure, as long as
    the glyph is inside "dimensions" given.
    """

    def __init__(self, dimensions):
        dict.__init__(self)
        self.dimensions = dimensions

    def __missing__(self, key):
        if (0 <= key[0] < self.dimensions[0]) \
            and (0 <= key[1] < self.dimensions[1]):
            return config.TRANSPARENT_GLYPH
        else:
            raise IndexError("The key %s is not a valid entry in this %s glyphMap."
                % (str(key), str(self)))

    def getArray(self):
        ret_array = arrays.empty_str_array(self.dimensions)
        for key in self:
            ret_array[key] = self[key]

        return ret_array
