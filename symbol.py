"""
'symbol' handles tiles and such.

Right now, it's pretty boring, as symbols that represent characters are just
one-element strings.
"""

REMEMBERED_COLOR = (99, 99, 99)

class Glyph(object):
    """
    The symbol that represents a character.
    """

    def __init__(self, char, color):
        """
        char - the character of the glyph.
        color - the color of the glyph, a 3-tuple of 0 to 255 ints..
        """

        self.char = char
        self.color = color
        self.r = color[0]
        self.g = color[1]
        self.b = color[2]

BAD_GLYPH = ('!', 255, 0, 0)
