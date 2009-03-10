"""
'symbol' handles tiles and such.

Right now, it's pretty boring, as symbols that represent characters are just
one-element strings.
"""

class Glyph(str):
    """
    The symbol that represents a character.
    
    At some point, this will become important, but right now I just want to be
    able to assign dudes glyphs and know that it won't all break horribly
    later on.
    """
    pass
