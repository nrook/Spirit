"""
Contains a number of helpful functions for working with 2-D arrays, especially
arrays of characters.  Arrays of characters are arrays of one-element strings.
"""

import coordinates
import numpy
import config
import exc
import symbol

def index(element, array):
    """
    Find and return integers x, y such that array[x,y] == element.
    If no such integers exist, raise an exception.
    """

    result = find(element, array)
    if result is None:
        raise IndexError("Element %s is not present in the array."
                         % str(element))
    
    return result

def find(element, array):
    """
    Find and return integers x, y such that array[x,y] == element.
    If no such integers exist, return None.
    """

    for x in range(array.shape[0]):
        for y in range(array.shape[1]):
            if array[x,y] == element:
                return (x,y)

    return None

def overlay(arrays, heights):
    """
    Return a tuple of two arrays representing a top-down view of the arrays
    supplied.  The first array is an array of strings, and represents the
    top-down view; the second is an array of integers, whose contents
    represent which array each character in the first array came from.

    For instance:
    arrays = [|a  |  |b b|
              |  a|, |b b|]
    heights = [2, 5]

    overlay(arrays, heights) = (|a b|  |2 5|
                                |b a|, |5 2|)

    Note that a lesser number represents an array more likely to be seen,
    and a greater number represents an array less likely to be seen.
    If heights is not sorted in ascending order, a ValueError will be
    raised.
    """

    sorted_heights = list(heights)
    sorted_heights.sort()
    if sorted_heights != list(heights):
        raise ValueError("List of heights %s is not in ascending order."
                         % str(heights))
    if len(arrays) != len(heights):
        raise ValueError("There are %d arrays, but there are %d heights!"
                         % (len(arrays), len(heights)))

    trans = config.TRANSPARENT_GLYPH
    composite_array = empty_str_array(arrays[0].shape)
    height_array = numpy.zeros(arrays[0].shape, 'i')
    reversed_arrays = list(arrays)
    reversed_arrays.reverse()
    reversed_heights = list(heights)
    reversed_heights.reverse()

    for i in range(len(reversed_arrays)):
        for x in range(reversed_arrays[0].shape[0]):
            for y in range(reversed_arrays[0].shape[1]):
                if reversed_arrays[i][x,y] != trans:
                    composite_array[x,y] = reversed_arrays[i][x,y]
                    height_array[x,y] = reversed_heights[i]

    return (composite_array, height_array)

def fovize(arr, view, memory_arr = None, memory = None, memory_color = (0, 0, 0)):
    """
    Returns a copy of arr with only the points in view visible.

    Note that despite its wide scope, this function should be fairly fast.

    If memory_arr is provided, then if a coordinate is not in "view" but is in
    "memory," a colored version of that coordinate in memory_arr is displayed
    instead.

    arr - an array.
    view - an iterable object full of points (tuples of coordinates).  Normally
        this is a fov object, but that is not necessary.
    memory_arr - an array.
    memory - an iterable object full of points.
    memory_color - the color which displayed things from memory will be painted.

    Returns - a copy of arr, except that each point in arr which is not in view
        is replaced with a transparent character, or a colored copy of a point
        in memory_arr, if applicable.
    """

    ret_array = empty_str_array(arr.shape)
    for coord in view:
        ret_array[coord] = arr[coord]

    for coord in memory:
        if coord not in view:
            ret_array[coord] = symbol.Glyph(memory_arr[coord].char, memory_color)

    return ret_array

def empty_str_array(dimensions):
    """
    Return an array such that empty_str_array(x,y).shape == (x,y) and with
    appropriate a,b, empty_str_array(x,y)[a,b] == config.TRANSPARENT_GLYPH.
    """

    ret_array = numpy.empty(dimensions, 'O')
    for x in range(dimensions[0]):
        for y in range(dimensions[1]):
            ret_array[x,y] = config.TRANSPARENT_GLYPH
    return ret_array

def print_str_to_end_of_line(initial_coords, string_used, array, color = (255, 255, 255)):
    """
    Print "string_used" to "array".  The first character of string_used is
    printed to array[initial_coords], the second to
    array[initial_coords[0] + 1, initial_coords[1]], etc.  The rest of the
    line in the array after the string will be filled with the transparent
    character.  If there is not enough room in the array for the string, a
    ValueError will be thrown.

    initial_coords - the coordinates to which the first character of the
        string should be printed.
    string_used - the string printed to the array.
    array - the array of characters (1-character strings) to which the
        string is printed.
    color - the color of the text being printed.
    """
    
# overflow chars = chars in array line - chars before string - chars in string
    overflow_chars = array.shape[0] - initial_coords[0] - len(string_used)
    if overflow_chars < 0:
        raise ValueError(
        "String of length %d starting at %d needs more than %d array size."
        % (len(string_used), initial_coords[0], array.shape[0]))

    printed_str = string_used + config.TRANSPARENT_GLYPH.char

    print_str(initial_coords, printed_str, array, color)

    return

def print_str(initial_coords, string_used, array, color = (255, 255, 255)):
    """
    Print "string_used" to "array".  The first character of string_used is
    printed to array[initial_coords], the second to
    array[initial_coords[0] + 1, initial_coords[1]], etc.  The rest of the
    line in the array after the screen will be unchanged.  If the string
    does not fit in the array, a ValueError will be thrown.

    initial_coords - the play in the array where the first character of the
        string is printed.
    string_used - the string to be printed to the array.
    array - the array to which the string is printed.
    color - the color of the string being printed.
    """

    if initial_coords[0] + len(string_used) > array.shape[0]:
        raise ValueError(
        "String of length %d starting at %d needs more than %d array size."
        % (len(string_used), initial_coords[0], array.shape[0]))

    for i in range(len(string_used)):
        array[initial_coords[0] + i, initial_coords[1]] = symbol.Glyph(string_used[i], (color[0], color[1], color[2]))

    return

def copy_array_centered_at(dst_nw_corner, block_dims, src_center, src_array, 
                           dst_array):
    """
    Copy the array src_array into a block_dims-sized rectangle of dst_array,
    with the information being copied in centered at src_center.

    dst_nw_corner - the corner closest to (0, 0) of the rectangle of dst_array
        which will be overwritten.
    block_dims - the dimensions of the rectangle of dst_array which will be
        overwritten.
    src_center - the coordinates of the square at the center of the rectangle
        of src_array which will be copied into dst_array.
    src_array - the source array.
    dst_array - the destination array.
    """

    src_rect = coordinates.centeredRect(src_center, block_dims)
    src_nw_corner = src_rect[0]
    copy_array_subset_lenient(src_nw_corner, dst_nw_corner, block_dims, 
                              src_array, dst_array)
    return

def copy_array_subset_lenient(src_nw_corner, dst_nw_corner, block_dims,
                              src_array, dst_array):
    """
    Copy a block_dims-sized subset of the array src_array into a
    block_dims-sized rectangle of the array dst_array, starting from
    src_nw_corner to dst_nw_corner, respectively.

    src_nw_corner - the corner closest to (0, 0) of the rectangle being copied
        out of src_array.
    dst_nw_corner - the corner closest to (0, 0) of the rectangle being
        overwritten in dst_array.
    block_dims - the dimensions of the rectangle being copied.
    src_array - the source array.
    dst_array - the destination array.
    """

    if block_dims[0] < 0 or block_dims[1] < 0:
        raise ValueError("block_dims = %s contains a coordinate less than 0."
                         % str(block_dims))
    
    src_nw_corner = list(src_nw_corner)
    dst_nw_corner = list(dst_nw_corner)
    block_dims = list(block_dims)

    for i in (0, 1):
        if src_nw_corner[i] < 0:
            src_nw_corner[i] = 0
# Set block_dims so that new_block_dims[i] + the amount shaved off by
# src_nw_corner[i] being less than 0 = old_block_dims[i]
            block_dims[i] = block_dims[i] + src_nw_corner[i]
        if src_nw_corner[i] + block_dims[i] > src_array.shape[i]:
# Set block_dims so that 
# new_block_dims[i] + src_nw_corner[i] = src_array.shape[i]
            block_dims[i] = src_array.shape[i] - src_nw_corner[i]
        if dst_nw_corner[i] < 0:
            dst_nw_corner[i] = 0
            block_dims[i] = block_dims[i] + dst_nw_corner[i]
        if dst_nw_corner[i] + block_dims[i] > dst_array.shape[i]:
            block_dims[i] = dst_array.shape[i] - dst_nw_corner[i]

    src_nw_corner = tuple(src_nw_corner)
    dst_nw_corner = tuple(dst_nw_corner)
    block_dims = tuple(block_dims)

    copy_array_subset(src_nw_corner, dst_nw_corner, block_dims, 
                      src_array, dst_array)

    return

def copy_array_subset(src_nw_corner, dst_nw_corner, block_dims,
                      src_array, dst_array):
    """
    This function differs only from copy_array_subset_lenient in that it
    raises exceptions whenever the coordinates given refer to squares not
    actually in the arrays provided.
    """

    exc.check_in_array(src_nw_corner, src_array.shape)
    exc.check_in_array(dst_nw_corner, dst_array.shape)
    exc.check_in_array(coordinates.add(coordinates.add(
                                   src_nw_corner, block_dims),
                   (-1, -1)), src_array.shape)
    exc.check_in_array(coordinates.add(coordinates.add(
                                   dst_nw_corner, block_dims),
                   (-1, -1)), dst_array.shape)

    for x in range(block_dims[0]):
        for y in range(block_dims[1]):
            dst_array[coordinates.add(dst_nw_corner, (x,y))] = \
                src_array[coordinates.add(src_nw_corner, (x,y))]

    return

def copy_entire_array(dst_nw_corner, src_array, dst_array):
    """
    Copy the entire array, src_array, into dst_array, with
    src_array[0,0] == dst_array[dst_nw_corner], etc.
    
    dst_nw_corner - a tuple of integers representing the coordinates
        into which src_array[0,0] will be copied.
    src_array - the array to be copied.
    dst_array - the array into which src_array is copied.
    """

    copy_array_subset((0, 0), dst_nw_corner, src_array.shape,
                      src_array, dst_array)
