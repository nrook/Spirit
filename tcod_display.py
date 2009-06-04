"""
A module to do various things with the Doryen library.
"""

import arrays
import config

import libtcodpy as tcod

level_cache = None

def init():
    tcod.console_init_root(80, 24, "Because It's There", False)

def refresh():
    tcod.console_flush()

def wait_for_key():
    """
    Get a keypress from the user, and return its code (an integer).
    """

    key = tcod.console_wait_for_keypress(False)
    return key.c

def yes_no(messages, question):
    raise NotImplementedError()

def get_direction(messages, question):
    raise NotImplementedError()

def display_array(array):
    """
    Copy the array of 1-character strings supplied to the screen, and flush.
    """

    for x in range(80):
        for y in range(24):
            tcod.console_put_char(None, x, y, ord(array[x,y]), tcod.BKGND_NONE)

    refresh()

    return

def refresh_screen(current_level = None):
    """
    Refresh the console with the Level object provided.
    If the Level is None, use the previous Level used instead.  If there is no
    previous Level, raise a LookupError.
    """
    global level_cache

    if current_level is None:
        if level_cache is None:
            raise LookupError("refresh_screen() has not yet been called!")
        else:
            current_level = level_cache

    level_cache = current_level

    display_main_screen(current_level.getFOVArray(),
                        current_level.getPlayer().coords,
                        current_level.messages.getArray(),
                        current_level.getPlayer().getSidebar().getArray())

def display_main_screen(level_array, level_center, 
                        message_array, sidebar_array):
    """
    Refresh the console with the three arrays provided.
    """
    assert message_array.shape == config.MESSAGES_DIMENSIONS
    assert sidebar_array.shape == config.STATUS_DIMENSIONS

    disp_array = arrays.empty_str_array(config.DEFAULT_DIMENSIONS)
    arrays.copy_array_centered_at((0, 0), config.MAP_DIMENSIONS, level_center, level_array, disp_array)
    arrays.copy_entire_array((60, 0), sidebar_array, disp_array)
    arrays.copy_entire_array((0, 17), message_array, disp_array)
    display_array(disp_array)

    return
