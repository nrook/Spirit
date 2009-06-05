import coordinates
from level import OPEN_GLYPHS

class fov(object):
    """
    An object representing a dude's field of view.  Contains two pieces of
    state: the coordinates which the dude can see, and the monsters which the
    dude can see.

    Public state:
    dudes: a frozenset of the dudes visible in the field of view, not including
        the dude doing the looking.
    """

# Private state:
# __the_field: a set containing the coordinates visible.

    def __init__(self):
        self.__the_field = set()

    def __contains__(self, key):
        """
        Return true if the coordinates given or the dude given is in view.

        key: a dude or a tuple of coordinates.
        """

        try:
            key.isPlayer() # check if key is a dude
        except AttributeError:
            return self.dudes.__contains(key)
        else:
            return self.__the_field.__contains__(key)

    def __iter__(self):
        return self.__the_field.__iter__()

    def recalculate(self, level_, initial_location):
        """
        Set this fov to the squares seen from initial_location on level_.

        level_ - The level on which the field of view is being calculated.
        initial_location - the viewpoint from which the field of view is being
            calculated.
        """
        
        dimensions = level_.dimensions
        border = set()
        fov_set = set()
        dude_set = set()

        border.add(initial_location)

        while len(border) != 0:
            next_border = set()
            for i in border:
                for adjacent in coordinates.adjacent_coords(i):
                    if adjacent in fov_set or adjacent in border or adjacent in next_border:
                        pass
                    elif not coordinates.legal(adjacent, dimensions):
                        pass
                    else:
                        if level_.dungeonGlyph(adjacent) in OPEN_GLYPHS:
                            next_border.add(adjacent)
                        else:
                            fov_set.add(adjacent)
                        if adjacent in level_.dudeLayer:
                            dude_set.add(level_.dudeLayer[adjacent])

                fov_set.add(i)

            border = next_border

        self.__the_field = fov_set
        self.dudes = frozenset(dude_set)
