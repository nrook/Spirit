"""
A module to do various things with the Doryen library.
"""

import libtcodpy as tcod

def init():
    tcod.console_init_root(80, 24, "Because It's There", False)

def wait_for_key():
    """
    Get a keypress from the user, and return its code (an integer).
    """

    key = tcod.console_wait_for_keypress(False)
    return key.c

def display_array(array):
    """
    Copy the array of 1-character strings supplied to the screen, and flush.
    """

    for x in range(80):
        for y in range(24):
            tcod.console_put_char(None, x, y, ord(array[x,y]), tcod.BKGND_NONE)
    
    # doesn't work tcod.refresh()

    return

def display_main_screen(level_array, level_center, 
                        message_array, sidebar_array):
    """
    Refresh the console with the three arrays provided.
    """

    disp_array = arrays.empty_str_array(config.DEFAULT_DIMENSIONS)
    disp_array.copy_array_centered_at((0, 0), config.MAP_DIMENSIONS, level_center, level_array, disp_array)
    disp_array.copy_entire_array((60, 0), config.STATUS_DIMENSIONS, sidebar_array, disp_array)
    disp_array.copy_entire_array((0, 17), config.MESSAGES_DIMENSIONS, message_array, disp_array)
    display_array(disp_array)

    return
