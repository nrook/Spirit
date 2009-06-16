"""
Contains the Dude class, which is a generic creature, and its children.

All players and monsters should be derived from Dude.
"""

import sys
import copy

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
import kb
kp = kb.kp

import log

"""
The speed system of this game is simple enough.

Time is measured by a measure called a "tick."  There are 144 ticks in a round;
once the round is over, the tick count resets.  (There is no significance to
the number of rounds that have transpired.)  144 is a nice, easy number that
is divisible by 2 and 3 many times, which is why it was picked.

A dude's "speed" is measured by how many ticks it takes for it to act again.
An ordinary dude has speed 12.

6x   - 2
4x   - 3
3x   - 4
2x   - 6
1.5x - 8
1x   - 12
0.66x- 18
0.5x - 24
0.25x- 48

I will probably ignore this whole comment.
"""

"""
Legal monster tags:
"proper_noun": this monster's name is a proper noun.
"""

PLAYER_GLYPH = symbol.Glyph('@', (255, 255, 255))

class Dude(fixedobj.FixedObject):
    """
    A generic creature; all players and monsters come from Dudes.
    
    The Dude class should not be instantiated as is; it exists only to have
    other classes derived from it.
    """
    def __init__(self, coords = (0, 0), glyph = symbol.BAD_GLYPH,
                 speed = 12, max_HP = 2, currentLevel = None, name = "Unnamed",
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

    def __init__(self, name, coords, speed = 12, currentLevel = None, char_level = 1, deck = None):
        if deck is None:
            deck = cards.Deck()

        max_HP = 24 + 6 * char_level

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

# First, get an action.  The entire purpose of these lines is to get an action
# which can then be performed.  If they return instead, they should return
# False, as no action has been performed.  Note that if the player is trying to
# do something that basically exists outside of the game world (like quitting
# or saving the game), there is no reason not to just let him do it within the
# getAction() function itself.
        cur_action = self.getAction()
        if cur_action.getCode() == "DO NOTHING":
            return False

        if cur_action.getCode() == "UP":

# Going up a level is an action which the Level being left cannot feasibly deal
# with.  As such, an exception is raised instead, to be caught in the main
# loop.
            raise exc.LevelChange()
        
# This used to be a call to do_generic_action.  I'm not sure why.
        return cur_action.do()
    
    def getAction(self):
        while 1:
            key = kb.getKey()
            if key == kp.QUIT:
                sys.exit(0)
            elif key == kp.SAVE:
                decision = kb.boolean_question(self.currentLevel.messages,
                    "Do you really want to save and quit the game?")
                if decision:
                    fileio.outputSave(self.currentLevel, "save.dat")
                    sys.exit(0)
                else:
                    self.currentLevel.messages.say("Never mind, then.")
                    return action.DoNothing()
            elif key == kp.WAIT:
                return action.Wait(self)
            elif key in config.DIRECTION_SWITCH:
                target = coordinates.add(self.coords,
                                         config.DIRECTION_SWITCH[key])
                if target in self.currentLevel.dudeLayer:
                    return action.Attack(self, 
                                         self.currentLevel.dudeLayer[target])
                else:
                    return action.Move(self, config.DIRECTION_SWITCH[key])
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
                    assert False
                assert False
            elif key == kp.UP:
                if self.currentLevel.elements[self.coords] == "<":
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
        AICode - a string representing the Monster's AI - "RANDOM", "CLOSE" etc.
        speed - just set this to 12 for now.
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
        self.spec = spec
        self.specfreq = specfreq
    
    def act(self):
        """
        Take a turn or do interface things, depending on what the player wants.

        Returns: True if the player has taken a turn; False otherwise.
        """
        self.resetFOV()
        cur_action = self.getAction()

        return cur_action.do()

        assert False, "An unexpected action was returned."

    def getAction(self):
        """
        Calculate the action of a monster.  AI code goes here!
        """
        
        if self.AICode == "RANDOM":
            return self.randomWalk()
                
        elif self.AICode == "CLOSE":
            return self.closeToPlayer()

        elif self.AICode == "RANGEDAPPROACH":
            return self.rangedApproach()
            
        else:
            return action.Wait(self)

    def randomWalk(self):
        """
        Return an action representing walking in a random direction.
        """
        while 1:
            coords = rng.choice(coordinates.DIRECTIONS)
            destination = coordinates.add(self.coords, coords)
            if destination == self.currentLevel.getPlayer().coords:
                action.Attack(self, self.currentLevel.player, 
                        "%(SOURCE_NAME)s attacks %(TARGET_NAME)s! (%(DAMAGE)d)")
            elif self.canMove(destination):
                return action.Move(self, coords)
            else:
                pass
    
    def closeToPlayer(self):
        """
        If the player is in sight, close in on him, and attack him if possible.
        
        If the player is not in sight, move randomly.
        This function returns an Action representing doing this.
        """
        playerLocation = self.currentLevel.getPlayer().coords

# If you can't see the player, move randomly.
        if self.currentLevel.getPlayer() not in self.fov.dudes:
            return self.randomWalk()

# If next to the player, attack him.
        if coordinates.adjacent(playerLocation, self.coords):
            if rng.percentChance(self.specfreq):
                return action.SpecialMelee(self,
                        self.currentLevel.player,
                        self.spec)
            else:
                return action.Attack(self, self.currentLevel.player, 
                    "%(SOURCE_NAME)s attacks %(TARGET_NAME)s! (%(DAMAGE)d)")
            
        bestMoves = []
        bestDistance = coordinates.distance(playerLocation, self.coords)            
        for possibleMove in coordinates.getDirections():
            destination = coordinates.add(self.coords, possibleMove)
            currentDistance = coordinates.distance(
                              playerLocation,
                              destination)
            if currentDistance == bestDistance and \
               self.canMove(destination):
                   
                bestMoves.append(possibleMove)
            elif currentDistance < bestDistance and \
               self.canMove(destination):
                
                bestMoves = [possibleMove]
                bestDistance = currentDistance
            
        if bestMoves == []:
            return self.randomWalk()
        else:
            return action.Move(self, rng.choice(bestMoves))

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
                possible_targets = [coordinates.add(self.coords, i) for i in possible_directions if self.canMove(coordinates.add(self.coords, i))]
                visible_targets = [coords for coords in possible_targets if coords in self.fov]
                close_targets = [coords for coords in visible_targets if (coordinates.minimumPath(coords, self.currentLevel.player.coords) <= 1)]
                actual_targets = [coords for coords in close_targets if not events.is_grenade_at_coords(coords, self.currentLevel)]
                if len(actual_targets) == 0:
                    return None
                final_target = rng.choice(actual_targets)
                return action.ThrowGrenade(self, final_target, 10)
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
    
#    def __init__(self, *args, **kwds):
#        return list.__init__(self, *args, **kwds)

    def getRandomMonster(self):
        """
        Get a duplicate of a random monster in the MonsterFactory.
        """

        prototype = rng.choice(self)
        return duplicate(prototype)
    
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
