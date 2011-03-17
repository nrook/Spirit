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
    RN,
    RNE,
    RE,
    RSE,
    RS,
    RSW,
    RW,
    RNW,
    QUIT,
    WAIT,
    SAVE,
    YES,
    NO,
    UP,
    CARD_1,
    CARD_2,
    CARD_3,
    CARD_4,
    CARD_5,
    CARD_6,
    CARD_7,
    ESCAPE,
    FIRE,
    HEAL,
    ) = range(33)

mainScreenTranslationTable = {
ord('k') : kp.N,
ord('u') : kp.NE,
ord('l') : kp.E,
ord('n') : kp.SE,
ord('j') : kp.S,
ord('b') : kp.SW,
ord('h') : kp.W,
ord('y') : kp.NW,
ord('K') : kp.RN,
ord('U') : kp.RNE,
ord('L') : kp.RE,
ord('N') : kp.RSE,
ord('J') : kp.RS,
ord('B') : kp.RSW,
ord('H') : kp.RW,
ord('Y') : kp.RNW,

ord('q') : kp.QUIT,
ord('.') : kp.WAIT,
ord('S') : kp.SAVE,
ord('<') : kp.UP,
ord('f') : kp.FIRE,
ord('v') : kp.FIRE,
ord('r') : kp.HEAL,
ord('1') : kp.CARD_1,
ord('2') : kp.CARD_2,
ord('3') : kp.CARD_3,
ord('4') : kp.CARD_4,
ord('5') : kp.CARD_5,
ord('6') : kp.CARD_6,
ord('7') : kp.CARD_7,
}

booleanQuestionTranslationTable = {
ord('y') : kp.YES,
ord('Y') : kp.YES,
ord('n') : kp.NO,
ord('N') : kp.NO,
}

directionTranslationTable = {
27       : kp.ESCAPE,
ord('k') : kp.N,
ord('u') : kp.NE,
ord('l') : kp.E,
ord('n') : kp.SE,
ord('j') : kp.S,
ord('b') : kp.SW,
ord('h') : kp.W,
ord('y') : kp.NW,
}

cardTranslationTable = {
27       : kp.ESCAPE,
ord('1') : kp.CARD_1,
ord('2') : kp.CARD_2,
ord('3') : kp.CARD_3,
ord('4') : kp.CARD_4,
ord('5') : kp.CARD_5,
ord('6') : kp.CARD_6,
ord('7') : kp.CARD_7,
}

# Translation table name translation table,
# used to select which translation table to use.
tTables = {
"main" : mainScreenTranslationTable,
"boolean" : booleanQuestionTranslationTable,
"direction" : directionTranslationTable,
"card" : cardTranslationTable,
}

# "Card switch"--maps card invocation keys to numbers, from 0 to 6.
card_values = {
    kp.CARD_1 : 0,
    kp.CARD_2 : 1,
    kp.CARD_3 : 2,
    kp.CARD_4 : 3,
    kp.CARD_5 : 4,
    kp.CARD_6 : 5,
    kp.CARD_7 : 6,
}

DIRECTION_SWITCH =  {
                    kp.NW: (-1, -1),
                    kp.W: (-1, 0),
                    kp.SW: (-1, 1),
                    kp.S: (0, 1),
                    kp.SE: (1, 1),
                    kp.E: (1, 0),
                    kp.NE: (1, -1),
                    kp.N: (0, -1),
                    kp.ESCAPE: None,
                    }

import tcod_display as display

def isCard(key):
    """
    Return true if key represents a card, no otherwise.
    """

    return key in card_values

def getKey(mode = "main"):
    """Get a keypress.  "mode" is a string indicating the used key table."""
    
    key = display.wait_for_key()
    usedTranslationTable = tTables[mode]
    if key in usedTranslationTable:
        return usedTranslationTable[key]
    else:
        return kp.NOTKEY

def question(messages, prompt, mode = "main"):
    """
    Ask a question by adding a message to the messageBuffer and updating it,
    then recording the keypress made in response.

    messages - the MessageBuffer to be used.
    prompt - the message to be displayed to the player to prompt a response.
    mode - the key table to be used to interpret the keypress made.
    """
    
    messages.say(prompt)

    response_key = getKey(mode)
    return response_key

def boolean_question(messages, prompt):
    """
    Ask a yes or no question, requesting an answer y, Y, n, or N.
    
    messages - the MessageBuffer upon which the question is asked.
    prompt - the message to be displayed to the player to prompt a response.

    Return true if the player answers "yes," and false if the player answers
    "no."
    """

    response_key = question(messages, prompt, "boolean")

# If an invalid response is given, keep asking until you get a valid one.
    while response_key == kp.NOTKEY:
        response_key = question(messages,
            "Please answer yes or no (y/n).",
            "boolean")
    
    assert response_key in [kp.YES, kp.NO]
    if response_key == kp.YES:
        return True
    else:
        return False

def direction_question(messages, prompt):
    """
    Ask a question whose response should be a valid direction.
    
    messages - the MessageBuffer upon which the question is asked.
    prompt - the message to be displayed to the player to prompt a response.

    Return a tuple of coordinates representing the direction the player
    chose. Return None if the player chose no direction.
    """

    response_key = question(messages, prompt, "direction")

# If an invalid response is given, keep asking until you get a valid one.
    while response_key == kp.NOTKEY:
        response_key = question(messages,
            "Please respond with a valid direction.",
            "direction")
    
    return DIRECTION_SWITCH[response_key]

def card_question(messages, prompt, deck):
    """
    Ask for the player to select a card.

    Returns the ID (0-6) of the card if an actual card is selected,
    -1 otherwise.

    messages - the MessageBuffer upon which the question is asked.
    prompt - the message to be displayed to the player to prompt a response.
    """

    response_key = question(messages, prompt, "card")

# If an invalid response is given, keep asking until you get a valid one.
    if response_key == kp.NOTKEY:
        messages.say("Please select a card (1-7) or escape.")
        return card_question(messages, prompt, deck)
    if response_key == kp.ESCAPE:
        messages.say("Never mind.")
        return -1

# Now we are guaranteed that response_key is in card_values.
    card_id = card_values[response_key]
    if card_id >= len(deck.hand):
        messages.say("You don't have a card there.")
        return card_question(messages, prompt, deck)
    else:
        return card_id

def pause(messages):
    """
    Ask for a keypress, not caring what it is.
    """

    question(messages, "--MORE--")
    messages.archive()
