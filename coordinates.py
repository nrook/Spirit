"""
Includes methods for dealing with tuples of coordinates.
"""

DIRECTIONS = ((-1, -1),
              (-1, 0),
              (-1, 1),
              (0, 1),
              (1, 1),
              (1, 0),
              (1, -1),
              (0, -1))

import rng

def add(coord1, coord2):
    """Add two 2D coordinates together."""
    return (coord1[0] + coord2[0], coord1[1] + coord2[1])

def subtract(coord1, coord2):
    """Subtract coord2 from coord1."""
    retList = []
    for i in range(len(coord1)):
        retList.append(coord1[i] - coord2[i])
    return tuple(retList)

def multiply(coord, scalar):
    """Multiply coord by scalar."""
    return (coord[0] * scalar, coord[1] * scalar)

def addCoords(coord1, coord2):
    """Depreciated."""
    return add(coord1, coord2)

def getDirections():
    """
    Returns a tuple of the eight directions.
    
    That is, ((-1, -1), (-1, 0), etc.)
    """
    return DIRECTIONS

def adjacent(coord1, coord2):
    """
    Returns True if coord1 is less than 1.5 away from coord2.
    
    Returns False otherwise.
    """
    
    return (distance(coord1, coord2) < 1.5)

def adjacent_coords(coord):
    """
    Return a tuple of the eight coordinates adjacent to the coordinate given.
    
    Note that adjacent_coords may return coordinates like (-1, 0).
    """

    return [(coord[0] + i[0], coord[1] + i[1]) for i in DIRECTIONS]

def adjacent_coords_sorted(coord, primary_direction):
    """
    Return a tuple of the eight coordinates adjacent to the coordinate given.

    coord - a coordinate
    primary_direction - a "unit vector" ((1,0), (-1,1), etc.)

    Returns: The eight coordinates adjacent to coord, so that the coordinate in
        primary_direction is listed first, then the rest of the coordinates, in
        order of their proximity to the one in primary_direction.
    """

    def sorting_function(x, y):
        (d_x, d_y) = (distance(primary_coordinate, x), distance(primary_coordinate, y))
        if d_x < d_y:
            return -1
        elif d_x == d_y:
            return 0
        else:
            return 1

    primary_coordinate = add(coord, primary_direction)
    adjacents = adjacent_coords(coord)
    return sorted(adjacents, sorting_function)

def radius(rad, coords, dimensions = None):
    """
    Return a set containing those coordinates rad away from a square.

    Note that radius does not use Euclidean distance.  For instance, the eight
    squares surrounding a square are all interpreted as being distance 1 away
    from that square.

    rad - the radius of the circle to be returned.
    coords - the coordinates at the center of the circle.
    dimensions - the dimensions of the plane on which the circle is being made.
        This is used so that the circle returned does not include nonexistent
        coordinates, like (20, 20) on a 9x9 square.  If dimensions = None, no
        checking for invalid coordinates will be done, so even coordinates like
        (0, -1) may be returned.
    """
    
    ret_set = set()
    if dimensions == None:
        for x in range(coords[0] - rad, coords[0] + rad + 1):
            for y in range(coords[1] - rad, coords[1] + rad + 1):
                ret_set.add((x, y))
    else:
        for x in range(max(coords[0] - rad, 0), min(coords[0] + rad, dimensions[0] - 1) + 1):
            for y in range(max(coords[1] - rad, 0), min(coords[1] + rad, dimensions[1] - 1) + 1):
                ret_set.add((x, y))

    return ret_set


def distance(coord1, coord2):
    """Return the distance between two points, as a float."""
    
    distance = 0
    for i in range(len(coord1)):
        distance += (coord2[i] - coord1[i])**2
    distance **= 0.5
    return distance

def are_diagonally_adjacent(coord1, coord2):
    """
    Return True if coord1 and coord2 are diagonally adjacent, false otherwise.
    """

    return (abs(coord1[0] - coord2[0]) == 1 and abs(coord1[1] - coord2[1]) == 1)

def get_cardinal_direction(coord1, coord2):
    """
    Get the direction from coord1 to coord2.

    A "cardinal direction" is a direction such as (1, 1), (1, 0), (0, -1), etc.
    If coord2 is in such a direction from coord1, this function returns it.  If
    not, it returns None.
    """

    difference = subtract(coord2, coord1)
    if difference[0] == 0:
        if difference[1] > 0:
            return (0, 1)
        elif difference[1] < 0:
            return (0, -1)
        else:
            return None
    elif difference[1] == 0:
        if difference[0] > 0:
            return (1, 0)
        elif difference[0] < 0:
            return (-1, 0)
        else:
            return None
    elif abs(difference[0]) == abs(difference[1]):
        return (difference[0]/abs(difference[0]), difference[1]/abs(difference[1]))
    else:
        return None

def minimumPath(coord1, coord2):
    """
    Return the minimum number of steps required to connect two coordinates.

    A step is a single move in any of the eight directions (N, NW, etc.).
    """

    return max(abs(coord2[0] - coord1[0]), abs(coord2[1] - coord1[1]))

def centeredRect(center, dimensions):
    """
    Get the coordinates of a rectangle centered at center.
    
    centeredRect() returns a tuple with the upper left corner of the
    rectangle as its first element and the lower right as its second.
    If the dimensions are even, the algorithm puts the centered square at the
    upper-left corner of the center.

    Note that centeredRect() will not always return valid coordinates -
    sometimes, it may return negative coordinates.
    """
    
    if dimensions[0] % 2 == 0:
        upperLeftX = center[0] - ((dimensions[0] - 2) / 2)
        lowerRightX = center[0] + ((dimensions[0]) / 2)
    else:
        upperLeftX = center[0] - ((dimensions[0] - 1) / 2)
        lowerRightX = center[0] + ((dimensions[0] - 1) / 2)
    
    if dimensions[1] % 2 == 0:
        upperLeftY = center[1] - ((dimensions[1] - 2) / 2)
        lowerRightY = center[1] + ((dimensions[1]) / 2)
    else:
        upperLeftY = center[1] - ((dimensions[1] - 1) / 2)
        lowerRightY = center[1] + ((dimensions[1] - 1) / 2)
    
    return ((upperLeftX, upperLeftY), (lowerRightX, lowerRightY))

def legal(coord, map_size):
    """
    Return 'true' if coord refers to a legal set of coordinates in an array
    of coordinates map_size.
    """

    return (coord[0] >= 0) and (coord[1] >= 0) and (coord[0] < map_size[0]) and (coord[1] < map_size[1])

def stringToCoords(coordString):
    """
    Given a string of the form "(a,b)", returns the tuple (a,b).
    """
    
    splitString = coordString.split(',')
    firstElement = int(splitString[0][1:])
    lastElement = int(splitString[1][:-1])
    return (firstElement, lastElement)
