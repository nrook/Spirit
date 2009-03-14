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

def distance(coord1, coord2):
    """Return the distance between two points, as a float."""
    
    distance = 0
    for i in range(len(coord1)):
        distance += (coord2[i] - coord1[i])**2
    distance **= 0.5
    return distance

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

def stringToCoords(coordString):
    """
    Given a string of the form "(a,b)", returns the tuple (a,b).
    """
    
    splitString = coordString.split(',')
    firstElement = int(splitString[0][1:])
    lastElement = int(splitString[1][:-1])
    return (firstElement, lastElement)
