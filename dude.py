"""
Contains the Dude class, which is a generic creature, and its children.

All players and monsters should be derived from Dude.
"""

import sys
import copy

import rng
import config
import symbol
import fixedobj
import action
import coordinates
import fileio
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



class Dude(fixedobj.FixedObject):
    """
    A generic creature; all players and monsters come from Dudes.
    
    The Dude class should not be instantiated as is; it exists only to have
    other classes derived from it.
    """
    def __init__(self, coords = (0, 0), glyph = symbol.Glyph('!'),
                 speed = 12, maxHP = 2, currentLevel = None, name = "Unnamed",
                 attack = 1, defense = 0, tags = None, char_level = 1,
                 passableTerrain = (symbol.Glyph('#'),symbol.Glyph('.'))):
        
        fixedobj.FixedObject.__init__(self, coords, glyph, currentLevel)
        self.name = name
        self.speed = speed
        self.passableTerrain = passableTerrain
        self.maxHP = maxHP
        self.curHP = self.maxHP
        self.attack = attack
        self.defense = defense
        self.char_level = char_level
        self.tags = tags if tags is not None else []
    
    def __str__(self):
        return "%s\nID %s\nSpeed %s\nCoordinates: %s\nTags: %s" % (self.glyph, self.ID, self.speed, self.coords, self.tags)
    
    def isTurn(self, tickno):
        return (tickno % speed == 0)
    
    def act(self):
        #Do not call this!
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
        
        return self.curHP <= 0
    
    def checkDeath(self):
        """If dead, die."""
        if self.isDead():
            self.die()
    
    def isPlayer(self):
        """Returns True if this Dude is the player, False otherwise."""
        
        return False #Player class contains an implementation that returns True
    
    def setHP(self, newHP):
        """
        Set the dude's HP to newHP or to its maxHP, whichever is lower.
        """
        if newHP > self.maxHP:
            self.curHP = self.maxHP
        else:
            self.curHP = newHP

class Player(Dude):
    """
    The player, or at least his representation in the game.
    
    There should only be one player, obviously.
    """
    
    def __init__(self, name, coords, speed = 12, currentLevel = None, char_level = 1, max_HP = None):
        if max_HP == None:
        	max_HP = 12 + 6 * char_level

        Dude.__init__(self, coords, symbol.Glyph('@'), speed, max_HP, currentLevel, name, 40, 100, ["proper_noun"], char_level)
    
    def getName(self, commonNounPreceder = "the"):
        return "you"
    
    def getAction(self):
        while 1:
            key = kb.getKey()
            if key == kp.QUIT:
                return action.Quit()
            elif key == kp.WAIT:
                return action.Wait()
            elif key in config.DIRECTION_SWITCH:
                if coordinates.add(self.coords, config.DIRECTION_SWITCH[key]) \
                    in self.currentLevel.dudeLayer:

                    return action.Attack(self.currentLevel.dudeLayer[coordinates.add(self.coords, config.DIRECTION_SWITCH[key])])
                else:
                    return action.Move(config.DIRECTION_SWITCH[key])
            elif key == kp.UP:
                if self.currentLevel.elements[self.coords] == "<":
        	        return action.Up()
            elif key == kp.SAVE:
                if self.currentLevel.UI.prompt(
                    "Do you really want to save and quit the game?"):
            
                    fileio.outputSave(self.currentLevel, "save.dat")
                    sys.exit()
                else:
                    self.currentLevel.UI.messageBuffer.append(
                        "Never mind, then.")
                    self.currentLevel.UI.updateScreenFromPrimaryDisplay()
    
    def die(self):
        sys.exit()
    
    def isPlayer(self):
        """Returns True if this Dude is the player, False otherwise."""
        return True

    def levelUp(self):
        """Raise the player's level, thus boosting his HP and stats."""
        HP_boost = action.HP_on_level_gain()
        self.maxHP += HP_boost
        self.curHP += HP_boost
        self.char_level += 1



class Monster(Dude):
    """
    A dude not controlled by the player.  Typically an antagonist.
    """
    def __init__(self, name, coords, glyph, AICode, speed, maxHP, tags, attack, defense, char_level, currentLevel = None):

        Dude.__init__(self, coords, glyph, speed, maxHP, currentLevel, name,
            attack, defense, tags, char_level)
        
        self.AICode = AICode
    
    def getAction(self):
        """
        Calculate the action of a monster.  AI code goes here!
        """
        
        if self.AICode == "RANDOM":
            #Make a completely random move.
            while 1:
                coords = rng.choice(coordinates.DIRECTIONS)
                if self.canMove(coordinates.add(self.coords, coords)):
                    return action.Move(coords)
                
        elif self.AICode == "CLOSE":
            #Close on the player, approaching him every turn.
            playerLocation = self.currentLevel.getPlayer().coords
            
            #If next to the player, attack him.
            if coordinates.adjacent(playerLocation, self.coords):
                return action.Attack(self.currentLevel.player, 
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
                return action.Wait()
            else:
                return action.Move(rng.choice(bestMoves))
            
        else:
            return action.Wait()
    
    def die(self):
       self.currentLevel.removeDude(self)

class MonsterFactory(list):
    """
    Getting a monster from this factory with [] gives you a duplicate.
    """
    
#    def __init__(self, *args, **kwds):
#        return list.__init__(self, *args, **kwds)
    
    def create(self, key, coords = None, currentLevel = None):
        """
        Get a duplicate of the monster identified (by int or string) as key.
        """
        
        monsterPrototype = self.getPrototype(key)
        return Monster(monsterPrototype.name,
                       coords,
                       monsterPrototype.glyph,
                       monsterPrototype.AICode,
                       monsterPrototype.speed,
                       monsterPrototype.maxHP,
                       monsterPrototype.tags[:] if monsterPrototype.tags is not None else None,
                       monsterPrototype.attack,
                       monsterPrototype.defense,
                       monsterPrototype.char_level,
                       currentLevel,
                      )
    
    def getPrototype(self, key):
        """
        Get the actual monster stored in the factory, not just a duplicate.
        """
        
        try: #is the key a string?
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
    

