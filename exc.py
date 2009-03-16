"""
Contains a bunch of functions to throw an exception if their arguments
hold to some condition.

In general, if a function in this module asks for a "name" parameter,
it wants a label to apply to the parameter to be tested, so that the
exception thrown can identify said parameter.
"""

class LevelChange(Exception):
    """Raised when the player moves up a level."""

class InvalidDataWarning(RuntimeWarning):
    """
    Raised when a dubious situation arises from outside data.

    Note that if the situation is bad, a plain old exception should be thrown,
    not this warning.  This warning should only be thrown if data is read that
    is comprehensible, but a bit odd, like a nonzero chance of activating a
    "NONE" special ability.
    """

def check_in_array(coord, shape, name = "The coordinates"):
    """
    Raise a ValueError if coord lies outside the array whose shape is shape.
    """

    for i in (0, 1):
        if coord[i] < 0 or coord[i] > shape[i]:
            raise ValueError("%s, %s, are outside the array of size %s."
                % (name, str(coord), str(shape)))

    return

def check_if_none(dict_of_maybe_none_things):
    """
    Raise a TypeError if any of the values in dict_of_maybe_none_things are
    actually None.  The key of said value is used to identify it.

    dict_of_maybe_none_things - a dictionary, with strings for keys and objects
        (that might be None) for values.  The key of each value refers to a
        description of it, in string form.
    """

    for pair in dict_of_maybe_none_things.items():
        if pair[1] is None:
            raise TypeError("%s is None, and shouldn't be." % pair[0])

    return
