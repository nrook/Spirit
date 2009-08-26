"""
Contains the Dude class, which is a generic creature, and its children.

All players and monsters should be derived from Dude.
"""

import sys
import copy
import collections

import tcod_display as display
import exc
import rng
import config
import symbol
import level
import fixedobj
import action
import coordinates
import arrays
import fileio
import cards
import fov
import events
import pf
import cond
import kb
kp = kb.kp

import log

"""
Legal monster tags:
"proper_noun": this monster's name is a proper noun.
"two_square_thrower": this monster has a projectile thrown two squares forward
    onto an empty or occupied space.
"bug_monster": this monster should only be generated when a bug has occurred
    (i.e. there is no "real" monster available).
"""

PLAYER_GLYPH = symbol.Glyph('@', (255, 255, 255))

class ais:
    """
    A glorified enum of AI states.
    """

    (FIGHTING,  # The monster sees an enemy.
     TRAVELING, # The monster is traveling to a specific square.
     WANDERING, # The monster is moving, but not to a specific square.
     RESTING,   # The monster is not moving.
     ) = range(4)

class Dude(fixedobj.FixedObject):
    """
    A generic creature; all players and monsters come from Dudes.
    
    The Dude class should not be instantiated as is; it exists only to have
    other classes derived from it.
    """
    def __init__(self, coords = (0, 0), glyph = symbol.BAD_GLYPH,
                 speed = 72, max_HP = 2, currentLevel = None, name = "Unnamed",
                 attack = 1, defense = 0, tags = None, char_level = 1,
                 passableTerrain = level.PASSABLE_TERRAIN):
        
        fixedobj.FixedObject.__init__(self, coords, glyph, currentLevel)
        self.name = name
        self.speed = speed
        self.passableTerrain = passableTerrain
        self.max_HP = max_HP
        self.cur_HP = self.max_HP
        self.attack = attack
        self.defense = defense
        self.char_level = char_level
        self.tags = tags if tags is not None else []
        self.fov = fov.fov()
        self.condition_list = []
    
    def __str__(self):
        return "%s\nID %s\nSpeed %s\nCoordinates: %s\nTags: %s" % (self.glyph, self.ID, self.speed, self.coords, self.tags)
    
    def isTurn(self, tickno):
        return (tickno % speed == 0)
    
    def act(self):
        raise NotImplementedError("Only implemented by Dude's children.")
    
    def getAction(self):
        """
        Return an Action that represents what the dude is going to do.
        """
        raise NotImplementedError("Only implemented by Dude's children.")
    
    def getName(self, commonNounPreceder = "the"):
        """
        Returns the dude's name, preceding it with commonNounPreceder.
        
        commonNounPreceder is ignored if the dude contains the proper_noun tag.
        Note that commonNounPreceder and the name itself are separated by a
        space.  If commonNounPreceder is "a", "an" will be substituted where
        appropriate.
        """
        
        if "proper_noun" in self.tags:
            return self.name
        else:
            if commonNounPreceder == "a" and self.name.startswith(("a", "e", "i", "o", "u")):
                return "an" + " " + self.name
            else:
                return str(commonNounPreceder) + " " + self.name
    
    def canMove(self, moveCoords):
        """
        Returns True if a move to moveCoords is possible; false otherwise.
        """
        
        return self.currentLevel.canMove(self, moveCoords)

    def possibleMoves(self):
        """
        Return a list of the possible moves from the current location.
        """

        adjacent_coords = coordinates.adjacent_coords(self.coords)
        return [x for x in adjacent_coords if self.canMove(x)]
    
    def canPass(self, dungeonGlyph):
        return dungeonGlyph in self.passableTerrain
    
    def isDead(self):
        """
        Returns True if HP <= 0, or if the dude is dead for some other reason.
        """
        
        return self.cur_HP <= 0
    
    def checkDeath(self):
        """If dead, die."""
        if self.isDead():
            self.die()
    
    def isPlayer(self):
        """Returns True if this Dude is the player, False otherwise."""
        
        return False # Player class contains an implementation that returns True
    
    def setHP(self, newHP):
        """
        Set the dude's HP to newHP or to its max_HP, whichever is lower.
        """
        if newHP > self.max_HP:
            self.cur_HP = self.max_HP
        else:
            self.cur_HP = newHP

    def resetFOV(self):
        """
        Reset the dude's field of view, determined by its current level and
        its coordinates.
        """

        self.fov.recalculate(self.currentLevel, self.coords)

    def giveCondition(self, condition):
        """
        Apply a new condition to the Dude.
        """

        for i in self.condition_list:
            if condition.name == i.name:
                self.condition_list.remove(i)
                break
        self.condition_list.append(condition)

    def hasCondition(self, condition_name):
        """
        Return True if the Dude has a condition of the name "condition_name".
        """

        return condition_name in [i.name for i in self.condition_list]

    def updateConditions(self):
        """
        Update all of the conditions, and remove them if necessary.
        """

        conditions_to_be_removed = []

        for condition in self.condition_list:
            condition.passTurn()
            if condition.isOver():
                conditions_to_be_removed.append(condition)

        for condition in conditions_to_be_removed:
            self.condition_list.remove(condition)

    def getConditionAction(self):
        """
        Get an action governed by the Dude's condition, not its decisions.

        Return an action if the Dude's conditions are making it take an action.
        Return "None" if they are not.
        """
        possible_actions = []
        for condition in self.condition_list:
            new_action = condition.getAction(self)
            if new_action is not None:
                possible_actions.append(new_action)

        if len(possible_actions) > 0:
            return rng.choice(possible_actions)
        else:
            return None

class Player(Dude):
    """
    The player, or at least his representation in the game.
    
    There should only be one player, obviously.

    Fields:
    Dude fields are still present.
    deck: the player's deck of cards.
    fractional_HP: a float from 0 to 1, representing a fractional bit of HP.
        Significant only in that when fractional_HP is high, the player will
        soon regenerate a point of HP.
    self.memory: a set of coordinates representing those places the player has
        seen.
    """

    REGENERATION_FACTOR = 0.01

    def __init__(self, name, coords, speed = 72, currentLevel = None, char_level = 1, deck = None):
        if deck is None:
            deck = cards.Deck()

        max_HP = 12 + 6 * char_level
        if config.WIZARD:
            max_HP += 200

        Dude.__init__(self, coords, PLAYER_GLYPH, speed, max_HP, currentLevel, name, 40, 100, ["proper_noun"], char_level)

        if currentLevel is not None:
            self.__sidebar = Sidebar(name, currentLevel.floor, char_level, 
                                     cur_HP, max_HP)
        else:
# If there is not yet a currentLevel to ask which floor you're on yet, put off
# generating the Sidebar until it is first needed.
            self.__sidebar = None

        self.deck = deck
        self.fractional_HP = 0.0

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
                           "self.deck":self.deck})

        self.__sidebar = Sidebar(self.name, self.currentLevel.floor,
                                 self.char_level, self.cur_HP, self.max_HP,
                                 self.deck)
    
    def getName(self, commonNounPreceder = "the"):
        return "you"

    def regenerate(self):
        """
        Restore a small fraction of the player's health.
        """

        true_hp = self.cur_HP + self.fractional_HP
        true_hp += self.max_HP * self.REGENERATION_FACTOR
        self.cur_HP = int(true_hp)
        if self.cur_HP == self.max_HP:
            self.fractional_HP = 0
        else:
            self.fractional_HP = true_hp - self.cur_HP

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
            return False

        if cur_action.getCode() == "UP":

# Going up a level is an action which the Level being left cannot feasibly deal
# with.  As such, an exception is raised instead, to be caught in the main
# loop.
            raise exc.LevelChange()
        
        action_succeeded = cur_action.do()
        if action_succeeded:
            self.updateConditions()

        return action_succeeded
    
    def getAction(self):
        while 1:
            key = kb.getKey()
# If the key is the quit key, quit.
            if key == kp.QUIT:
                sys.exit(0)
# If the key is the save key, ask if the player wants to save, and do so.
            elif key == kp.SAVE:
                decision = kb.boolean_question(self.currentLevel.messages,
                    "Do you really want to save and quit the game?")
                if decision:
                    fileio.outputSave(self.currentLevel, "save.dat")
                    sys.exit(0)
                else:
                    self.currentLevel.messages.say("Never mind, then.")
                    return action.DoNothing()
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
# If the key is a card key, use the card.
            elif key in kb.card_values:
                card_id = kb.card_values[key]
                
                if card_id >= len(self.deck.hand):
                    return action.DoNothing()
                card_to_use = self.deck.hand[card_id]

# If the card is directional, get the direction to use it in.
                if card_to_use.is_directional:
                    direction_of_target_square = kb.direction_question(
                        self.currentLevel.messages,
                        "In which direction would you like to use the %s card?"
                        % card_to_use.ability_name)
                if card_to_use.is_melee:
                    target_square = coordinates.add(self.coords, direction_of_target_square)
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
                        target_square = coordinates.add(self.coords, coordinates.multiply(direction_of_target_square, 2))
                        if self.currentLevel.isEmpty(target_square) and (not events.is_grenade_at_coords(target_square, self.currentLevel)):
                            del self.deck.hand[card_id]
                            return action.ThrowGrenade(self, target_square, 10)
                        else:
                            self.currentLevel.messages.say("There's something in the way!")
                            return action.DoNothing()
                    elif card_to_use.action_code == "ARROW":
                        return action.FireArrow(self, direction_of_target_square, 12)
                    assert False
                assert False
            elif key == kp.REST:
# Give the player the "rest" status, so she waits until healed fully.
                self.giveCondition(cond.Resting())
                return action.Wait(self)
# If the key is the "go upstairs" key, try to go up a level.
            elif key == kp.UP:
                if self.currentLevel.elements[self.coords] == level.UPSTAIRS_GLYPH:
        	        return action.Up()

    def obtainCard(self, mon):
        """
        Obtain the card related to mon, and shuffle it into the deck library.
        """
        self.deck.randomInsert(cards.mon_card(mon))
    
    def die(self):
        print "Ack!  You died!"
        sys.exit()
    
    def isPlayer(self):
        """Returns True if this Dude is the player, False otherwise."""
        return True

    def levelUp(self):
        """Raise the player's level, thus boosting his HP and stats."""
        HP_boost = action.HP_on_level_gain()
        self.max_HP += HP_boost
        self.cur_HP += HP_boost
        self.char_level += 1

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

class Monster(Dude):
    """
    A dude not controlled by the player.  Typically an antagonist.
    """
    def __init__(self, name, coords, glyph, AICode, speed, max_HP, tags, attack, defense, char_level, spec, specfreq, currentLevel = None):
        """
        Create a new monster.

        name - the name of the monster.
        coords - the coordinates at which the monster currently is.
            (5, 9), for instance.
        glyph - a one-character string representing the monster, like "d".
        AICode - a string representing the Monster's AI - "CLOSE", etc.
        speed - just set this to 72 for now.
        max_HP - the maximum (and starting) HP of the monster.
        tags - any special qualities the monster has.
        attack - the monster's attack capability; what percentage of the health
            of a player of the same level the monster should take away.  An
            integer.
        defense - what percentage of the damage dealt by the player the monster
            should take.  An integer; <100 shows resilience, while >100 shows
            a faculty for taking much damage.
        char_level - the dungeon level the monster should normally appear on;
            also relates to its power.
        spec - a string representing the monster's special power, activated on
            a regular attack.
        specfreq - a string representing how many of the monster's regular
            melee attacks should be replaced by a special attack.
        """

        Dude.__init__(self, coords, glyph, speed, max_HP, currentLevel, name,
            attack, defense, tags, char_level)
        
        self.AICode = AICode
        self.state = ais.RESTING
        self.player_last_location = None
        self.spec = spec
        self.specfreq = specfreq
    
    def act(self):
        """
        Asks the monster to take a turn.

        Returns: True is the monster has taken a turn via this call,
            False otherwise.
        """
        self.resetFOV()
        cur_action = self.getAction()

        for condition in self.condition_list:
            cur_action = condition.modifyAction(cur_action)

        action_succeeded = cur_action.do()
        if action_succeeded:
            self.updateConditions()

        return action_succeeded

    def getAction(self):
        """
        Calculate the action of a monster.  AI code goes here!
        """
        
        if self.state == ais.FIGHTING:
            return self.fighting()
        elif self.state == ais.TRAVELING:
            return self.traveling()
        elif self.state == ais.WANDERING:
            return self.wandering()
        elif self.state == ais.RESTING:
            return self.resting()
        else:
            assert False, "This monster has some strange, unknown AI state!"

    def fighting(self):
        """
        Calculate the action of a monster who sees the player.
        """
        
        if self.currentLevel.player not in self.fov:
            if self.player_last_location is not None:
# The player has escaped!  Find a likely square where he could have gone.
                adjacent_coords = coordinates.adjacent_coords(self.player_last_location)
                legal_coords = [i for i in adjacent_coords if coordinates.legal(i, self.currentLevel.dimensions)]
                passable_coords = [i for i in legal_coords if self.currentLevel.isEmpty(i)]
                out_of_vision_coords = [i for i in passable_coords if i not in self.fov]

                if len(out_of_vision_coords) > 0:
# There is a possible escape route!  Pursue!
                    self.direction = coordinates.subtract(rng.choice(out_of_vision_coords), self.player_last_location)
                    self.path = pf.find_shortest_path(self.currentLevel, self.coords, self.player_last_location, False)
                    if self.path == []:
# There is no route to the player's escape route.  Wait, but stay in
# state FIGHTING so as to take advantage of any route that opens up.
                        return action.Wait(self)
                    self.state = ais.TRAVELING
                    return self.traveling()
                else:
# There is no possible escape route; give up and rest.
                    self.state = ais.RESTING
                    return self.resting()

            else:
                assert False

        else:
            self.player_last_location = self.currentLevel.player.coords

            if self.AICode == "CLOSE":
                return self.closeToPlayer()

            elif self.AICode == "RANGEDAPPROACH":
                return self.rangedApproach()
            
            else:
                raise exc.InvalidDataWarning(
                    "The monster %s has an unknown AICode, %s"
                    % (self.name, self.AICode))
                return action.Wait(self)

        assert False

    def traveling(self):
        """
        Calculate the action of a monster moving to a specific location.

        Note that a "path" variable must exist for this to make sense.
        """

# self.path[0] should be the monster's current square.
# self.path[1] should be the square the monster wants to move to.
# self.path[-1] should be the monster's ultimate destination.

        assert self.path != None, "Despite the monster being in state TRAVELING, the path variable is null."

        print "Beginning to travel."
        
        if self.currentLevel.player in self.fov:
            print "The player is in view!"
            self.state = ais.FIGHTING
            return self.fighting()
        else:
            print "Starting invalid path determination.."
            path_is_invalid = False

            if len(self.path) == 0:
                print "len(self.path) == 0"
                assert False # This shouldn't happen!
                path_is_invalid = True
            elif self.coords != self.path[0]:
                print "self.path[0] doesn't correspond to the actual path!"
# Something has moved the monster since its last turn.
                path_is_invalid = True
            elif len(self.path) == 1:
                print "the monster has reached its destination!"
# Since self.coords == self.path[0], the monster has reached its destination!
                self.state = ais.WANDERING
                return self.wandering()
            elif not self.canMove(self.path[1]):
                print "The monster can't make it to self.path[1]."
                path_is_invalid = True

            if path_is_invalid:
                print "The path is invalid!"
                if len(self.path) == 0:
                    print "The path is empty!"
# If the path is completely empty, something has gone wrong.
                    assert False
# Just give up and return to being stationary.
                    self.state = ais.RESTING
                    return self.resting()
                else:
                    print "The path has a destination."
                    destination = self.path[-1]
                    self.path = pf.find_shortest_path(self.currentLevel, self.coords, destination, True)
                    if len(self.path) == 0:
# There simply is no path to the destination!
# Set self.path to only contain the destination, so that next turn, this code
# attempts to find another path.
                        print "There's no path to the destination!  Wait."
                        self.path = [destination]
                        return action.Wait(self)
                    elif len(self.path) == 1:
                        print "The path has only one square, for some reason."
# This should not happen!
                        assert False
                        return action.Wait(self)

            if self.canMove(self.path[1]):
                print "Moving on the path!"
                move_direction = coordinates.subtract(self.path[1], self.coords)
                self.path.pop(0)
                return action.Move(self, move_direction)
            else:
                print "Can't move on the path!"
                assert False, "The supposedly legal path contains an illegal move!"
                return action.Wait(self)

    def wandering(self):
        """
        Calculate the action of a monster without a specific goal in mind.
        """

        if self.currentLevel.player in self.fov:
            self.state = ais.FIGHTING
            return self.fighting()

        assert self.direction is not None

        ordered_moves = coordinates.adjacent_coords_sorted(self.coords, self.direction)
        possible_moves = [x for x in ordered_moves if self.currentLevel.canMove(self, x)]
        if len(possible_moves) == 0:
# You're stuck!  Give up, just rest there.
            self.state = ais.RESTING
            return self.resting()
        else:
            move_coords = possible_moves[0]
            self.direction = coordinates.subtract(move_coords, self.coords)
            return action.Move(self, coordinates.subtract(move_coords, self.coords))

        assert False

    def resting(self):
        """
        Return the action of a monster who is just sitting there, doing nothing.
        """

        if self.currentLevel.player in self.fov:
            self.state = ais.FIGHTING
            return self.fighting()
        else:
            return action.Wait(self)


    def closeToPlayer(self):
        """
        Pathfind to the player, and attack him if possible.
        """

        player_location = self.currentLevel.player.coords

# If adjacent to the player, attack him.
        if coordinates.adjacent(player_location, self.coords):
            if rng.percentChance(self.specfreq):
                return action.SpecialMelee(self,
                        self.currentLevel.player,
                        self.spec)
            else:
                return action.Attack(self, self.currentLevel.player, 
                    "%(SOURCE_NAME)s attacks %(TARGET_NAME)s! (%(DAMAGE)d)")

# Otherwise, pathfind toward him.
        else:
            path = pf.find_shortest_path(self.currentLevel, self.coords, player_location, False)
            if path != []:
                move_coords = coordinates.subtract(path[1], path[0])
                return action.Move(self, move_coords)
            else:
                return action.Wait(self)

    def rangedApproach(self):
        ranged_attack = self.probableRangedAttack()
        if ranged_attack is not None:
            return ranged_attack
        else:
            return self.closeToPlayer()
    
    def probableRangedAttack(self):
        """
        Return an action for a ranged attack on a target if such an attack is
        possible.  Otherwise, return None.
        """
        if "two_square_thrower" in self.tags:
            if self.currentLevel.player in self.fov \
                and coordinates.minimumPath(self.coords, self.currentLevel.player.coords) in range(1, 4):
                
                possible_directions = ((2,0),(2,2),(0,2),(-2,2),(-2,0),(-2,-2),(0,-2),(2,-2))
                possible_targets = [coordinates.add(self.coords, i) for i in possible_directions if self.currentLevel.isEmpty(coordinates.add(self.coords, i))]
                visible_targets = [coords for coords in possible_targets if coords in self.fov]
                close_targets = [coords for coords in visible_targets if (coordinates.minimumPath(coords, self.currentLevel.player.coords) <= 1)]
                actual_targets = [coords for coords in close_targets if not events.is_grenade_at_coords(coords, self.currentLevel)]
                if len(actual_targets) == 0:
                    return None
                final_target = rng.choice(actual_targets)
                return action.ThrowGrenade(self, final_target, 10)
            else:
                return None
        elif "twelve_square_firer" in self.tags:
            direction = coordinates.get_cardinal_direction(self.coords,
                          self.currentLevel.player.coords)
            dist = coordinates.minimumPath(self.coords,
                   self.currentLevel.player.coords)
            if self.currentLevel.player in self.fov \
                and direction is not None \
                and dist < 12:

                return action.FireArrow(self, direction, 12)
            else:
                return None
        else:
            return None
    
    def die(self):
        if self.spec != "NONE":
            self.currentLevel.player.obtainCard(self)
        self.currentLevel.removeDude(self)

class MonsterFactory(list):
    """
    Getting a monster from this factory with [] gives you a duplicate.
    """
    
# Represents the chances of finding a monster, relative to the difference
# between that monster's level and the dlvl it is found on.
    DLVL_RARITY = collections.defaultdict(lambda: 0,
                  {-2:1,
                   -1:3,
                    0:5,
                    1:3,
                    2:1,
                  })
    
    def __init__(self, *args, **kwds):
        """
        Create a new MonsterFactory, given a list of monsters (or nothing).
        """
        list.__init__(self, *args, **kwds)
        self.buggy_monster = None

    def getRandomMonster(self, dlvl):
        """
        Get a duplicate of a random monster in the MonsterFactory.
        """
        
        monster_selection_container, total = self.getMonsterSelection(dlvl)
        if total == 0 or len(monster_selection_container) == 0:
            return self.getBuggyMonster()

        random_number = rng.randInt(0, total - 1)
        for i in monster_selection_container:
            random_number -= i[0]
            if random_number < 0:
                return duplicate(i[1])

    def getMonsterSelection(self, dlvl):
        """
        Return a container representing the rarity of monsters on a level.

        dlvl - the level of the dungeon on which the monsters are appearing.

        returns - a tuple of the form
            ([(rarity_1, monster_1), ..., (rarity_k, monster_k)], total).
            rarity_x is an integer representing the chance that a monster
            will appear; higher is more likely.  total is the total rarity
            of all the monsters involved.
        """

        total = 0
        selection_list = []
        for i in self:
            rarity = self.DLVL_RARITY[i.char_level - dlvl]
            if rarity != 0:
                selection_list.append((rarity, i))
                total += rarity

        return (selection_list, total)
    
    def create(self, key, coords = None, currentLevel = None):
        """
        Get a duplicate of the monster identified (by int or string) as key.
        """
        
        monsterPrototype = self.getPrototype(key)
        return duplicate(monsterPrototype, coords, currentLevel)
    
    def getPrototype(self, key):
        """
        Get the actual monster stored in the factory, not just a duplicate.
        """
        
        try: # is the key a string?
            key.upper()
        except AttributeError:
            return list.__getitem__(self, key)
        else:
            soughtIndex = -1
            for mon in self:
                if key == mon.name:
                    soughtIndex = self.index(mon)
            if soughtIndex == -1:
                raise ValueError("No monster with name %s found." % key)
            else:
                return list.__getitem__(self, soughtIndex)

    def setBuggyMonster(self, buggy_monster):
        """
        Set the monster created when no valid monster data is available.
        """

        self.buggy_monster = buggy_monster

    def getBuggyMonster(self):
        """
        Get a copy of the monster created when no valid monster data is present.
        """

        return duplicate(self.buggy_monster)
    
class Sidebar(object):
    """
    A list of information, on the side of the screen, about the player.
    """

    def __init__(self, name, floor, char_level, cur_HP, max_HP, deck):
        """
        Initialize a Sidebar with the corresponding values.

        name - a string of the player's name.
        floor - an integer of the floor of the dungeon the player is on.
        char_level - an integer representing the player's character level.
        cur_HP - an integer; the player's current HP.
        max_HP - an integer; the player's maximum HP.
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
        arrays.print_str_to_end_of_line((1, 6),
            "Deck(%d):" % len(deck.library), self.__array)
        for i in range(len(deck.hand)):
            arrays.print_str_to_end_of_line((1, 7 + i),
                "(%d) %s" % (i+1, deck.hand[i].monster_name), self.__array)
        
        return

    def getArray(self):
        """
        Return an array representing the contents of this Sidebar.
        """
        return self.__array

def duplicate(prototype, coords = None, currentLevel = None):
        """
        Get a duplicate of the monster prototype supplied.  If a currentLevel
        is supplied as well, then the Monster is initialized on that Level; if
        coords are supplied, the Monster begins on those coordinates.
        """
        
        return Monster(prototype.name,
                       coords,
                       prototype.glyph,
                       prototype.AICode,
                       prototype.speed,
                       prototype.max_HP,
                       prototype.tags[:] if prototype.tags is not None else None,
                       prototype.attack,
                       prototype.defense,
                       prototype.char_level,
                       prototype.spec,
                       prototype.specfreq,
                       currentLevel,
                      )
