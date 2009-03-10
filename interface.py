import config
import log
import curses

class ScreenVariables:
    def __init__(self, xlength = -1, ylength = -1):
        self.xlen = xlength
        self.ylen = ylength
    
    def getxmax(self):
        return self.xlen - 1
    
    def getymax(self):
        return self.ylen - 1

def initialize(win):
    """
    Initialize, given stdscr (or what will be stdscr), initializes the display.
    
    Initialize will set all of the module variables, and get everything proper.
    """
    
    global sv
    global stdscr
    sv = ScreenVariables()
    stdscr = win
    
    (sv.ylen, sv.xlen) = stdscr.getmaxyx()
    curses.curs_set(0)

def fill(character, xmin, ymin, xmax, ymax, window = None):
    if window is None:
        window = stdscr
    
    try:
        for x in range(xmin, xmax + 1):
            for y in range(ymin, ymax + 1):
                window.addch(y, x, ord(character))
    except curses.error:
        if x != sv.getxmax() or y != sv.getymax():
            raise

def main(win):
    initialize(win)
    stdscr.refresh()
    
    for y in range(0, sv.ylen):
        for x in [x - 3 for x in range(3, sv.ylen, 4)]:
            stdscr.addstr(y, x, str(stdscr.getch()))

def update(panel):
    for y in range(len(panel) - 1):
        #Update the window for every line EXCEPT the final one.
        stdscr.addstr(y, 0, panel[y])
    try:
        stdscr.addstr(len(panel) - 1, 0, panel[len(panel) - 1][:-1])
    except curses.error:
        # Curses throws curses.error if I try to modify the last character.
        raise AttributeError("Tried to modify last character; this should never be thrown.")

def waitforq():
    while 1:
        c = stdscr.getch()
        if c == ord('q'):
            return

def getkey():
    while 1:
        c = stdscr.getch()
        return c

if __name__ == "__main__":
    curses.wrapper(main)
