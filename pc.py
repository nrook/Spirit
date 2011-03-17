import sys

import tcod_display as display
import exc
import rng
import config
import dude
import level
import action
import coordinates
import symbol
import arrays
import cards
import cond
import kb
kp = kb.kp

import log

PLAYER_GLYPH = symbol.Glyph('@', (255, 255, 255))

class Player(dude.Dude):
    """
    The player, or at least his representation in the game.
    
    There should only be one player, obviously.

    Fields:
    Dude fields are still present.
    deck: the player's deck of cards.
    self.memory: a set of coordinates representing those places the player has
        seen.
    """

    def __init__(self, name, coords, speed = 72, currentLevel = None, char_level = 1, deck = None):
        if deck is None:
            deck = cards.Deck()

        max_HP = 12 + 6 * char_level
        if config.WIZARD:
            max_HP += 200

        dude.Dude.__init__(self, coords, PLAYER_GLYPH, speed, max_HP, currentLevel, 
            name, 8, 100, ["proper_noun"], char_level)

        if currentLevel is not None:
            self.__sidebar = Sidebar(name, currentLevel.floor, char_level, 
                                     cur_HP, max_HP)
        else:
# If there is not yet a currentLevel to ask which floor you're on yet, put off
# generating the Sidebar until it is first needed.
            self.__sidebar = None

        self.deck = deck

        self.memory = set()
        self.fov.updateMemory(self.memory)

    def getSidebar(self):
        """
        Get the sidebar of this player, creating it if necessary.
        """

        self.updateSidebar()
        return self.__sidebar

    def updateSidebar(self):
        """
        Update the sidebar of this player, by setting all of its attributes
        to those attributes already possessed by the player.  Expects that all
        of the player's important attributes (most notably currentLevel)
        actually exist - that is, aren't just None.
        """
        
        exc.check_if_none({"self.name":self.name,
                           "self.currentLevel.floor":self.currentLevel.floor,
                           "self.char_level":self.char_level,
                           "self.cur_HP":self.cur_HP,
                           "self.max_HP":self.max_HP,
                           "self.deck":self.deck,
                           "self.conditions":self.conditions})

        self.__sidebar = Sidebar(self.name, self.currentLevel.floor,
                                 self.char_level, self.cur_HP, self.max_HP,
                                 self.deck, self.conditions.values())
    
    def getName(self, commonNounPreceder = "the"):
        return "you"

    def act(self):
        """
        Take a turn or do interface things, depending on what the player wants.

        Returns: True if the player has taken a turn; False otherwise.
        """
        self.resetFOV()

        display.refresh_screen(self.currentLevel)

# Clear the message buffer.
        self.currentLevel.messages.archive()

        cond_action = self.getConditionAction()
        if cond_action is None:
# First, get an action.  The entire purpose of these lines is to get an action
# which can then be performed.  If they return instead, they should return
# False, as no action has been performed.  Note that if the player is trying to
# do something that basically exists outside of the game world (like quitting
# or saving the game), there is no reason not to just let him do it within the
# getAction() function itself.
            cur_action = self.getAction()
        else:
            cur_action = cond_action

        if cur_action.getCode() == "DO NOTHING":
            return 0

        if cur_action.getCode() == "UP":
# Going up a level is an action which the Level being left cannot feasibly deal
# with.  As such, an exception is raised instead, to be caught in the main
# loop.
            raise exc.LevelChange()
        
        action_ticks = cur_action.do()
        if action_ticks != 0:
            self.updateConditions()

        return action_ticks
    
    def getAction(self):
        while 1:
            key = kb.getKey()
# If the key is the quit key, quit.
            if key == kp.QUIT:
                sys.exit(0)
# If the key is the save key, ask if the player wants to save, and do so.
            elif key == kp.SAVE:
                if self.currentLevel.elements[self.coords] == level.UPSTAIRS_GLYPH:
                    decision = kb.boolean_question(self.currentLevel.messages,
                        "Do you really want to save and quit the game?")
                    if decision:
                        raise exc.SavingLevelChange()
                    else:
                        self.currentLevel.messages.say("Never mind, then.")
                        return action.DoNothing()
                else:
                    self.currentLevel.messages.say("You can only save when on the stairs (<).")
# If the key is the wait key, wait.
            elif key == kp.WAIT:
                return action.Wait(self)
# If the key is a movement key, move or attack, as is appropriate.
            elif key in config.DIRECTION_SWITCH:
                target = coordinates.add(self.coords,
                                         config.DIRECTION_SWITCH[key])
                if target in self.currentLevel.dudeLayer:
                    return action.Attack(self, 
                                         self.currentLevel.dudeLayer[target])
                elif self.canMove(target):
 # If the player is stuck, he cannot move!
                    if self.hasCondition("stuck"):
                        self.currentLevel.messages.append("You are stuck and cannot move!")
                        return action.DoNothing()
                    else:
                        return action.Move(self, config.DIRECTION_SWITCH[key])
                else:
# A move is illegal!
                    return action.DoNothing()
            elif key in config.RUN_DIRECTION_SWITCH:
                direction = config.RUN_DIRECTION_SWITCH[key]
                target = coordinates.add(self.coords, direction)
                if len(self.fov.dudes) != 0:
                    self.currentLevel.messages.append("Not with enemies in view!")
                    return action.DoNothing()
                elif self.canMove(target):
# If the player is stuck, he cannot move.
                    if self.hasCondition("stuck"):
                        self.currentLevel.messages.append("You are stuck and cannot move!")
                        return action.DoNothing()
                    else:
                        self.giveCondition(cond.Running(direction))
                        return action.Move(self, direction)
# If the key requests that a card be used, prompt for a card, then use it.
            elif key == kp.FIRE:
                if len(self.deck.hand) == 0:
                    self.currentLevel.messages.append(
                        "You have no cards to use!")
                    return action.DoNothing()
                else:
                    card_id = kb.card_question(self.currentLevel.messages,
                        "Which card do you want to evoke?", self.deck)
                    if card_id == -1:
                        return action.DoNothing()
                    else:
                        return self.useCard(card_id)

            elif key == kp.HEAL:
# Have the player use a card to heal wounds.
                card_id = kb.card_question(self.currentLevel.messages, 
                            "Which card will you sacrifice for your health?",
                            self.deck)
                if card_id == -1:
                    return action.DoNothing()
                else:
                    del self.deck.hand[card_id]
                    return action.Heal(self, self, 
                        rng.XdY(2, 7 + self.char_level), False)
# If the key is the "go upstairs" key, try to go up a level.
            elif key == kp.UP:
                if self.currentLevel.elements[self.coords] == level.UPSTAIRS_GLYPH:
        	        return action.Up()

    def useCard(self, card_id):
        """
        Use a card (asking the player for required information).

        card_id - the ID (CARD_1, CARD_2, etc.) of the card to be used.
        
        Returns the action decided upon.
        """
        log.log("Using card (Card ID: %s)" % card_id)

        if card_id == -1 or card_id >= len(self.deck.hand):
            return action.DoNothing()
        else:
            card_to_use = self.deck.hand[card_id]

# If the card is directional, get the direction to use it in.
            if card_to_use.is_directional:
                direction_of_target_square = kb.direction_question(
                    self.currentLevel.messages,
                    "In which direction would you like to use the %s card?"
                    % card_to_use.ability_name)
                if direction_of_target_square is None:
                    self.currentLevel.messages.say("Never mind.")
                    return action.DoNothing()
            if card_to_use.is_melee:
                target_square = coordinates.add(
                    self.coords, direction_of_target_square)
                if target_square in self.currentLevel.dudeLayer:
                    del self.deck.hand[card_id]
                    return action.SpecialMelee(self,
                        self.currentLevel.dudeLayer[target_square],
                        card_to_use.action_code)
                else:
                    self.currentLevel.messages.say("You whiff completely!")
                    del self.deck.hand[card_id]
                    return action.Wait(self)
            else:
                if card_to_use.action_code == "GRENTHROW":
                    target_square = coordinates.add(self.coords, 
                        coordinates.multiply(direction_of_target_square, 2))
                    if self.currentLevel.isEmpty(target_square) \
                        and (not events.is_grenade_at_coords(
                        target_square, self.currentLevel)):

                        del self.deck.hand[card_id]
                        return action.ThrowGrenade(self, target_square)
                    else:
                        self.currentLevel.messages.say(
                            "There's something in the way!")
                        return action.DoNothing()
                elif card_to_use.action_code == "ARROW":
                    del self.deck.hand[card_id]
                    return action.FireArrow(
                        self, direction_of_target_square, 12)
                elif card_to_use.action_code == "POUNCE":
                    del self.deck.hand[card_id]
                    return action.Pounce(self, direction_of_target_square, 12)
                elif card_to_use.action_code == "HASTE":
                    del self.deck.hand[card_id]
                    return action.HasteMonster(self, self, 12)
                elif card_to_use.action_code == "HASTEALL":
                    del self.deck.hand[card_id]
                    return action.HasteAll(self, 8, True, True)
                assert False
            assert False

    def obtainCard(self, mon):
        """
        Obtain the card related to mon, and shuffle it into the deck library.
        """
        self.deck.randomInsert(cards.mon_card(mon))
    
    def die(self):
        raise exc.PlayerDeath()
    
    def isPlayer(self):
        """Returns True if this Dude is the player, False otherwise."""
        return True

    def levelUp(self):
        """Raise the player's level, thus boosting his HP and stats."""
        HP_boost = action.HP_on_level_gain()
        self.max_HP += HP_boost
        self.setHP(self.max_HP)
        self.char_level += 1
        self.currentLevel.messages.append("You feel stronger!")

    def resetFOV(self):
        """
        Reset the player's field of view, determined by its current level and
        its coordinates.  Unlike the generic dude version, also updates the
        player's memory.
        """
        
        self.fov.recalculate(self.currentLevel, self.coords)
        self.fov.updateMemory(self.memory)

    def clearMemory(self):
        """
        Clear the player's memory; appropriate when the player is going to a
        new level.
        """

        self.memory = set()

class Sidebar(object):
    """
    A list of information, on the side of the screen, about the player.
    """

    def __init__(self, name, floor, char_level, cur_HP, max_HP, deck, conditions):
        """
        Initialize a Sidebar with the corresponding values.

        name - a string of the player's name.
        floor - an integer of the floor of the dungeon the player is on.
        char_level - an integer representing the player's character level.
        cur_HP - an integer; the player's current HP.
        max_HP - an integer; the player's maximum HP.
        deck - the deck containing the player's cards.
        conditions - a list (NOT A DICTIONARY) of the player's conditions.
        """

        self.__array = arrays.empty_str_array(config.STATUS_DIMENSIONS)
        arrays.print_str_to_end_of_line((1, 0), name, self.__array)
        arrays.print_str_to_end_of_line((1, 1), "Floor %d" % floor,
                                        self.__array)
        arrays.print_str_to_end_of_line((1, 2), "Level %d" % char_level,
                                        self.__array)
        arrays.print_str_to_end_of_line((1, 4), 
                                        "HP: %d(%d)" % (cur_HP, max_HP),
                                        self.__array)

        condition_names = ""
        for c in conditions:
            c_name = c.getDisplayName()
            if c_name != "":
                if condition_names == "":
                    condition_names = c_name
                else:
                    condition_names = " ".join((condition_names, c_name))
        arrays.print_str_to_end_of_line((1, 5), condition_names, self.__array)

        arrays.print_str_to_end_of_line((1, 7),
            "Deck(%d):" % len(deck.library), self.__array)
        for i in range(len(deck.hand)):
            arrays.print_str_to_end_of_line((1, 8 + i),
                "(%d) %s" % (i+1, deck.hand[i].monster_name), self.__array)
        return

    def getArray(self):
        """
        Return an array representing the contents of this Sidebar.
        """
        return self.__array
