import coordinates
from level import OPEN_GLYPHS
import libtcodpy as tcod

FOV_RADIUS = 4

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
            return self.__the_field.__contains__(key)
        else:
            return self.dudes.__contains__(key)

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
        map = level_.sight_map

        tcod.map_compute_fov(map, initial_location[0], 
            initial_location[1], FOV_RADIUS, True, tcod.FOV_SHADOW)

        border = set()
        fov_set = set()
        dude_set = set()

        for i in range(initial_location[0] - FOV_RADIUS, 
            initial_location[0] + FOV_RADIUS + 1):

            for j in range(initial_location[1] - FOV_RADIUS,
                initial_location[1] + FOV_RADIUS + 1):
                    
                    if tcod.map_is_in_fov(map, i, j):
                        fov_set.add((i, j))
                        if (i, j) != initial_location and (i, j) in level_.dudeLayer:
                            dude_set.add(level_.dudeLayer[(i, j)])

        self.__the_field = fov_set
        self.dudes = frozenset(dude_set)

    def updateMemory(self, memory):
        """
        Add the coordinates in the FOV to a given set.

        memory - the set for the coordinates to be added to.
        """

        memory.update(self.__the_field)
