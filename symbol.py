"""
'symbol' handles tiles and such.

Right now, it's pretty boring, as symbols that represent characters are just
one-element strings.
"""

import struct

glyph_struct = struct.Struct("cBBB")
glyph_struct_size = glyph_struct.size

def englyph(char, color):
    """
    Transform a character and a color into a colored character string.

    char - a 1-character string representing the character of the glyph.
    color - a 3-element tuple of the form (r, g, b).
    """
    
    ret_val = glyph_struct.pack(char, color[0], color[1], color[2])
    while ret_val[-1] == '\x00':
        ret_val = ret_val[:-1]
    return ret_val

def deglyph(glyph):
    """
    Transform a glyph into a character and a color.
    
    glyph - the encoded glyph to be transformed into a color.

    Returns a 2-element tuple:
        (the character in the glyph;
         the color in the glyph, represented as a 3-integer tuple
        )
    """

    glyph = "".join((glyph, '\x00' * (glyph_struct_size - len(glyph))))
    unpacked = glyph_struct.unpack(glyph)
    return (unpacked[0], (unpacked[1], unpacked[2], unpacked[3]))

class Glyph(str):
    """
    The symbol that represents a character.
    
    At some point, this will become important, but right now I just want to be
    able to assign dudes glyphs and know that it won't all break horribly
    later on.
    """
    pass

BAD_GLYPH = englyph('!', (255, 0, 0))
