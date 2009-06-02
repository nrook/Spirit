"""
A random number generator, which includes various common functions.
"""

import random

def initialize(seed = None):
    """
    Initializes the RNG; supplies a random seed if none is provided.
    """
    
    random.seed(seed)

def randInt(start, stop):
    """
    Get a random integer in the range [start, stop].
    """
    
    return random.randint(start, stop)

def choice(sequence):
    """
    Return a random member of this sequence.
    """
    
    return random.choice(sequence)

def random_insert(list_, element):
    """
    Insert element into a random place in list_.

    list_ - the list (or other item that implements the list insert).
    element - the thing to inset into the list.
    """

    list_.insert(randInt(0, len(list_)), element)

def percentChance(percent_integer):
    """
    Has a percent_integer percent chance of returning True; otherwise, False.
    """
    
    return random.randint(1, 100) <= percent_integer

def XdY(X, Y):
    """Return X rolls of a Y-sided die, added together."""
    
    ret_value = 0
    for i in range(X):
        ret_value += randInt(1, Y)
        
    return ret_value

def randomPointInRect(nw_corner, se_corner):
    """
    Returns a random point within the box described, inclusive.
    """
    
    return (randInt(nw_corner[0], se_corner[0]), randInt(nw_corner[1], se_corner[1]))

if __name__ == "__main__":
    #Test suite.
    initialize()
    print randint(1, 10)
    print randint(1, 10)
    print randint(1, 10)
    print choice((5, 10, 15, 20, 25))
