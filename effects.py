"""
Creates and manages "special effects" to be used on the screen.
"""

import collections

import tcod_display as display
import threading
import config

BLINKING_TIME = 0.7

thr = None
ev = None

def init():
    """
    Initialize the thread responsible for animating effects.
    """

    global thr
    global ev

    ev = threading.Event()
    thr = threading.Thread(target=repeat, args=(ev, BLINKING_TIME, animate))
    thr.start()

def repeat(event):
    while True:
        event.wait(BLINKING_TIME)
        if event.isSet():
            break
        # do animation things

def stop():
    ev.set()
