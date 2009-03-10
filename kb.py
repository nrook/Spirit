"""
Get keypresses and translate them to easily-understood constants.
"""



class kp:
    """
    A glorified enum for keypress codes used by the program itself.
    
    Note that every function in kp returns kp codes rather than ord() codes or
    similar; this is so that the keyboard bindings can be changed just by
    changing kb, without having to dig around in the rest of the code.
    
    kp contains different code for keypresses on the main screen and keypresses
    on various other screens; this is so that a keypress can be rebinded on one
    screen without changing it everywhere else.
    """
    (
    NOTKEY,
    N,
    NE,
    E,
    SE,
    S,
    SW,
    W,
    NW,
    QUIT,
    WAIT,
    SAVE,
    YES,
    NO,
    UP,
    ) = range(15)

mainScreenTranslationTable = {
ord('k') : kp.N,
ord('u') : kp.NE,
ord('l') : kp.E,
ord('n') : kp.SE,
ord('j') : kp.S,
ord('b') : kp.SW,
ord('h') : kp.W,
ord('y') : kp.NW,
ord('q') : kp.QUIT,
ord('.') : kp.WAIT,
ord('S') : kp.SAVE,
ord('<') : kp.UP,
}

booleanQuestionTranslationTable = {
ord('y') : kp.YES,
ord('Y') : kp.YES,
ord('n') : kp.NO,
ord('N') : kp.NO,
}

#Translation table name translation table.
tTables = {
"main" : mainScreenTranslationTable,
"boolean" : booleanQuestionTranslationTable,
}

import interface

def getKey(mode = "main"):
    """Get a keypress.  "mode" is a string indicating the used key table."""
    
    key = interface.getkey()
    usedTranslationTable = tTables[mode]
    if key in usedTranslationTable:
        return usedTranslationTable[key]
    else:
        return kp.NOTKEY
