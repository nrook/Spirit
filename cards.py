import rng

MON_ABILITY_DICT = {
    "lancer" : {"code":"CRITICAL", "aname":"Damaging attack", "is_melee":True, "is_directional":True,},
    "boxer" : {"code":"KNOCK", "aname":"Punch", "is_melee":True, "is_directional":True,},
    "grenadier": {"code":"GRENTHROW", "aname":"Throw grenade", "is_melee":False, "is_directional":True,},
    "archer": {"code":"ARROW", "aname":"Fire arrow", "is_melee":False, "is_directional":True,},
    "spider": {"code":"STICK", "aname":"Spin web", "is_melee":True, "is_directional":True,},
    "tiger": {"code":"HASTE", "aname":"Haste", "is_melee":False, "is_directional":False,},
    "q.statue": {"code":"HASTEALL", "aname":"Quickening field", "is_melee":False, "is_directional":False,},
}

class Deck(object):
    """
    A Deck is a list of Cards held by the Player.

    It consists of two main groups: the Hand, which includes the cards the
    player can use right now, and the Library, which stores the rest.  The Hand
    can store a maximum of seven cards; every turn, if there is room, a card is
    moved from the Library to the Hand.  When the Player acquires a new Card by
    killing an enemy, this Card is inserted at a random position in the Library.

    Fields:
    hand - a list of the Cards in the Hand.  The first card in the hand is
        hand[0]; the last is hand[-1].
    library - a list of the Cards in the Library.  The lowest card in the
        library is hand[0]; the top card (i.e. the first to be drawn) is
        hand[-1].
    HAND_MAX_LENGTH - the maximum length of a hand.  Don't touch.
    """

    HAND_MAX_LENGTH = 7

    def __init__(self, hand_list = None, library_list = None):
        """
        Create a new Deck, with a hand composed of the cards in hand_list and a
        library composed of the cards in library_list.  If hand_list contains
        more than seven cards, a ValueError will be thrown.
        """

        if hand_list is None:
            hand_list = []
        if library_list is None:
            library_list = []
        
        if len(hand_list) > self.HAND_MAX_LENGTH:
            raise ValueError("The hand provided contains %d > %d objects."
                             % (len(hand_list), self.HAND_MAX_LENGTH))
        self.hand = [card for card in hand_list]
        self.library = [card for card in library_list]

    def randomInsert(self, card):
        """
        Insert the card given into a random part of the Library.
        """

        rng.random_insert(self.library, card)

    def draw(self):
        """
        If the Hand is not full, pop the top card off the Library and append it
        to the end of the Hand.  If the Hand is full, do nothing.  Return True
        if a card is drawn, and False if one is not.
        """
        if len(self.hand) < self.HAND_MAX_LENGTH:
            if len(self.library) >= 1:
                self.hand.append(self.library.pop())
                return True
            else:
                return False
        elif len(self.hand) == self.HAND_MAX_LENGTH:
            return False
        else:
            assert False, "The hand has more than %d cards!" \
                % self.HAND_MAX_LENGTH

class Card(object):
    """
    A thing held by the Player, used to activate some special ability.

    Fields:
    action_code - the special code of the special ability used.
    monster_name - the name of the monster from whom the card comes.
    ability_name - the name of the special ability the Card contains.
    is_directional - a boolean representing whether the player should specify
        which direction the card is being used.
    is_melee - a boolean representing whether the card is meant to be used
        against an adjacent foe.
    """

    def __init__(self, action_code, monster_name, ability_name, is_directional, is_melee):
        """
        Create a new Card, with the action code, monster name, and ability name
        specified.  For more information on these fields, see the general class
        description.
        """

        self.action_code = action_code
        self.monster_name = monster_name
        self.ability_name = ability_name
        self.is_directional = is_directional
        self.is_melee = is_melee

def mon_card(mon):
    """
    Return the card corresponding to the monster, "mon".
    """

    mon_attr_dict = MON_ABILITY_DICT[mon.name]
    return Card(mon_attr_dict["code"], mon.name, mon_attr_dict["aname"], mon_attr_dict["is_directional"], mon_attr_dict["is_melee"],)
