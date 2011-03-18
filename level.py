"""
level.py includes the Level class, which stores a specific dungeon level.
"""

import config
import arrays
import coordinates
import log
import msg
import symbol
import events
import effects
import queue
import dude
import rng

import numpy
import libtcodpy as tcod

ROOM_INTERIOR_GLYPH = symbol.Glyph('.', (255, 255, 255))
CORRIDOR_GLYPH = symbol.Glyph('#', (118, 41, 0))
UPSTAIRS_GLYPH = symbol.Glyph('<', (255, 0, 0))
DOWNSTAIRS_GLYPH = symbol.Glyph('>', (0, 255, 0))

OPEN_GLYPHS = set([ROOM_INTERIOR_GLYPH, CORRIDOR_GLYPH])
PASSABLE_TERRAIN = set([ROOM_INTERIOR_GLYPH, CORRIDOR_GLYPH])

class Level(object):
    """
    A Level is an object that represents the current state of a dungeon level.
    
    A Level consists of a list of Layers, and a Dungeon at the bottom.
    
    Fields:
    effects - an effectsMap containing the effects to be laid over the level.
    dudeLayer - the Layer containing Dudes and, of course, the player.
    elements - an array of characters containing terrain features which
        exist on top of ordinary terrain, like stairs.
    dungeon - an array of characters representing walls and floors.
    """
    """
    __composite_map - an array of strings, representing a top-down view of
        the Level, with the Dudes on top and the dungeon on the bottom.
    __height_map - an array of integers, representing the height of each
        tile of the __composite_map, that is, which part of the Level each
        tile came from.
    __are_maps_correct - a boolean.  If True, the __composite_map and
        __height_map are correct, and don't need to be refreshed.  If
        False, then they are incorrect, and refresh_maps() must be called
        before they are used.
    __SOLID_EFFECTS_HEIGHT - the height of solid effects.
    __DUDE_HEIGHT - the height of dudes.
    __ELEMENT_HEIGHT - the height of elements.
    __DUNGEON_HEIGHT - the height of terrain.
    """
    
    __SOLID_EFFECTS_HEIGHT = -1
    __DUDE_HEIGHT = 2
    __ELEMENT_HEIGHT = 5
    __DUNGEON_HEIGHT = 8
    
    def __init__(self, 
        dimensions, floor, dude_layer, elements, dungeon, definition):
        """
        Create a Level.

        dimensions - the actual dimensions of the Level, in (x, y) form.
        floor - the height of the Level in comparison to other Levels;
            an integer.
        dude_layer - a DudeLayer.  (If None, a DudeLayer will be created.)
        elements - an array representing the elements of the Level: terrain
            features which are overlaid upon the regular terrain, but which
            cannot be picked up like items.
        dungeon - an array representing the dungeon: the walls, floors, and
            other terrain.
        definition - a FloorDefinition for this Level.
        """

        if dude_layer is None:
            dude_layer = DudeLayer(None, dimensions)

        self.floor = floor
        self.dungeon = dungeon
        self.elements = elements
        self.dimensions = dimensions
        self.dudeLayer = dude_layer
        self.effects = effects.EffectsMap(dimensions)
        self.definition = definition
        self.player = None
        self.messages = msg.MessageBuffer(config.MESSAGES_DIMENSIONS)
        self.__composite_map = arrays.empty_str_array(dimensions)
        self.__height_map = numpy.zeros(dimensions, 'i')
        self.__are_maps_correct = False
        self.__queue = None
        self.events = [events.LevelTick(self)]
        self.time = 0

        self.sight_map = make_sight_map(dungeon)
    
    def __str__(self):
        return str(self.getArray())

    def __del__(self):
        """
        The sight map must be manually garbage-collected.
        """

        tcod.map_delete(self.sight_map)

    def __addCharacterToMap(self, glyph, coords, height):
        """
        Add a glyph to the composite and height maps.

        glyph - the glyph to be added to the maps.
        coords - the coordinates at which the glyph is to be added.
        height - the height at which the glyph is to be added.
        """

        if not self.__are_maps_correct: return

# Remember that small height means being near the top.
        if height <= self.__height_map[coords]:
            self.__composite_map[coords] = glyph
            self.__height_map[coords] = height

        return

    def __delCharacterFromMap(self, coords, height):
        """
        Delete the glyph specified from the composite and height maps,
        searching below it for a glyph to replace it.  If the glyph
        is below the glyph on the composite map, do nothing.
        """
        
        if not self.__are_maps_correct: return
        assert height >= self.__height_map[coords]

        if height == self.__height_map[coords]:
            (self.__composite_map[coords], self.__height_map[coords]) = \
                self.__getCharacterBelow(coords, height)

        return

    def __getCharacterBelow(self, coords, height):
        """
        Return the symbol and height of the highest non-transparent
        glyph at coords below height.  If no such character exists,
        return the transparent character and a very large height.

        coords - a tuple of integers representing the location of the
            glyph being searched for.
        height - an integer representing the (exclusive) lower limit
            of height for the glyph being looked for.
        
        Returns - a pair, containing a 1-character string (the glyph
            found) and an integer (its height).
        """
        
        if height < self.__SOLID_EFFECTS_HEIGHT:
            glyph = self.effects.get(coords)
            if glyph != config.TRANSPARENT_GLYPH:
                return (glyph, self.__SOLID_EFFECTS_HEIGHT)
        if height < self.__DUDE_HEIGHT:
            glyph = self.dudeGlyph(coords)
            if glyph != config.TRANSPARENT_GLYPH:
                return (glyph, self.__DUDE_HEIGHT)
        if height < self.__ELEMENT_HEIGHT:
            glyph = self.elementGlyph(coords)
            if glyph != config.TRANSPARENT_GLYPH:
                return (glyph, self.__ELEMENT_HEIGHT)
        if height < self.__DUNGEON_HEIGHT:
            glyph = self.dungeonGlyph(coords)
            if glyph != config.TRANSPARENT_GLYPH:
                return (glyph, self.__DUNGEON_HEIGHT)

        return (config.TRANSPARENT_GLYPH, self.__DUNGEON_HEIGHT + 1)

    def getArray(self):
        """
        Get an array representing a top-down view of the Level.

        Returns: An array of characters.
        """

        if not self.__are_maps_correct:
            self.refreshMaps()
        return self.__composite_map

    def getFOVArray(self, view = None):
        """
        Get an array representing those squares in the array visible.

        view - a fov containing the squares you want to be visible in the array.
               If view is None, the player's FOV is used.
        
        Returns: an array of characters.
        """
        
        view = view if view != None else self.getPlayer().fov
        return arrays.fovize(self.getArray(), view, self.dungeon, self.getPlayer().memory, symbol.REMEMBERED_COLOR)

    def dudeGlyph(self, coords):
        """
        Get the symbol representing the spot on the dudeLayer at coords.
        """
        
        if coords in self.dudeLayer:
            return self.dudeLayer[coords].getCurGlyph()
        else:
            return config.TRANSPARENT_GLYPH

    def elementGlyph(self, coords):
        """
        Get the symbol representing the spot on the element array at coords.
        """

        return self.elements[coords]

    def dungeonGlyph(self, coords):
        """
        Get the symbol representing the spot on the dungeon array at coords.
        """

        return self.dungeon[coords]

    def refreshMaps(self):
        maps = arrays.overlay((self.dudeLayer.getArray(), self.elements, 
            self.dungeon), (self.__DUDE_HEIGHT, self.__ELEMENT_HEIGHT,
            self.__DUNGEON_HEIGHT))
        self.__composite_map = maps[0]
        self.__height_map = maps[1]
        self.__are_maps_correct = True

        return
    
    def addDude(self, addedDude, coords = None, addToQueue = True):
        """
        Add a dude to the dudeLayer of this level, modifying all accordingly.
        
        If no coordinates are supplied, the current coordinates of the dude
        are used.
        """
        
        if coords is None:
            dudeCoords = addedDude.coords
            if dudeCoords is None:
                raise TypeError("Dude has no coordinates")
        else:
            dudeCoords = coords
        
        if dudeCoords in self.dudeLayer:
            raise AttributeError("A dude, %s, was already at %s." % (addedDude.getName("a"), dudeCoords))

        addedDude.setCurrentLevel(self)
        addedDude.setCoords(dudeCoords)
        self.dudeLayer.append(addedDude)
        self.__addCharacterToMap(addedDude.getCurGlyph(), dudeCoords, self.__DUDE_HEIGHT)
        if addToQueue:
            self.__queue.put(addedDude, self.time)
    
    def addPlayer(self, addedPlayer, coords = None):
        """
        Add a dude to this Level, and set it as the current player here.

        Note that the new player is not put on the queue!
        """
        self.player = addedPlayer
        self.dudeLayer.player = addedPlayer
        self.addDude(addedPlayer, coords, False)

    def refreshDudeGlyph(self, changed_dude):
        """
        Redraw a dude. Used if a dude's glyph may have changed.
        
        changed_dude - the dude to redraw.
        """

        assert self.dudeLayer[changed_dude.coords] is changed_dude

        self.__delCharacterFromMap(changed_dude.coords, self.__DUDE_HEIGHT)
        self.__addCharacterToMap(changed_dude.getCurGlyph(), changed_dude.coords, self.__DUDE_HEIGHT)

    def moveDude(self, movedDude, moveCoords):
        self.__delCharacterFromMap(movedDude.coords, self.__DUDE_HEIGHT)
        self.dudeLayer.moveObject(movedDude, moveCoords)
        self.__addCharacterToMap(movedDude.getCurGlyph(), movedDude.coords, self.__DUDE_HEIGHT)
    
    def getPlayer(self):
        """Returns the player dude."""
        
        return self.player
    
    def kill(self, target):
        """
        Remove an actor from the level.
        
        This will delete the actor entirely if no other references to it exist.
        Note that while kill() will delete the glyph of a dude, it will not
        delete the remaining glyphs from an event!  Any dying event must do its
        own dirty work.
        """
        something_was_killed = False
# If it's in the dudeLayer, remove it.
        if target in self.dudeLayer:
            self.dudeLayer.remove(target)
            something_was_killed = True
# If it's in the dudeLayer, it's on the map.
            self.__delCharacterFromMap(target.coords, self.__DUDE_HEIGHT)

# If it's an event, remove it.
        if target in self.events:
            self.events.remove(target)
            something_was_killed = True
        
# If it's in the queue, remove it from there.
        if target in self.__queue:
            self.__queue.erase(target)
            something_was_killed = True

        if not something_was_killed:
            raise ValueError("Couldn't kill %s." % target)

    def dungeonGlyph(self, coords):
        """
        Gets the particular glyph of a dungeon square.
        """
        
        return self.dungeon[coords]

    def addSolidEffect(self, coords, glyph):
        """
        Add a glyph to the level's solid effects map.

        glyph - the glyph to be displayed as a solid effect.
        coords - the coordinates at which the glyph should be displayed.
        """
        
        self.effects.add(coords, glyph)
        self.__addCharacterToMap(glyph, coords, self.__SOLID_EFFECTS_HEIGHT)

    def removeSolidEffect(self, coords, glyph = None):
        """
        Remove a glyph from the level's solid effects map.

        coords - the coords at which the glyph should be removed.
        glyph - the glyph to be removed.  If no glyph is supplied, then the top
            glyph is removed.
        """
        
        removed = self.effects.remove(coords, glyph)
        new_top = self.effects.get(coords)
        if new_top == config.TRANSPARENT_GLYPH:
            self.__delCharacterFromMap(coords, self.__SOLID_EFFECTS_HEIGHT)
        elif new_top == removed:
            pass
        else:
            self.__addCharacterToMap(new_top, coords, self.__SOLID_EFFECTS_HEIGHT)

    def are_immediately_accessible(self, coords1, coords2):
        """
        Returns true if a move from coords1 to coords2 is legal given the
        dungeon layout, false otherwise.

        This function does not take into account monsters on either square.
        """

               # the given coordinates are legal
        result = (all(map(self.legalCoordinates, (coords1, coords2))) and
               # the movedDude can move on the dungeon tile of moveCoords
                all(map(self.isEmpty, (coords1, coords2))) and
               # moveCoords is only one square away
                (coordinates.minimumPath(coords1, coords2) == 1))

        # a "corner move," of the following form, is NOT being performed
        # d.      (moving from s to d)
        # #s

        if coordinates.are_diagonally_adjacent(coords1, coords2):
            adjacent_squares = ((coords1[0], coords2[1]), (coords2[0], coords1[1]))
# Return true only if both adjacent squares are empty, i.e. disallow corner moves.
            result = result and all(map(lambda x: self.isEmpty(x), adjacent_squares))
        
        return result

    def canMove(self, movedDude, moveCoords):
        """
        Returns true if a move by movedDude to moveCoords is possible.
        
        Returns false otherwise.
        """

        return (self.are_immediately_accessible(movedDude.coords, moveCoords)
# either moveCoords is empty, or it's occupied by movedDude
               and ((moveCoords not in self.dudeLayer) or (self.dudeLayer[moveCoords] == movedDude)))

    def isEmpty(self, coords):
        """
        Returns true if a square contains an "empty" glyph.
        """
        return self.dungeonGlyph(coords) in PASSABLE_TERRAIN

    def immediately_accessible_squares(self, coords):
        """
        Returns a list of the squares walkable from the square at coords.

        This function does not take into account monsters present at the source
        or destination squares.
        """

        adjacent_coords = coordinates.adjacent_coords(coords)
        return [x for x in adjacent_coords if self.are_immediately_accessible(coords, x)]

    def legalCoordinates(self, coords):
        """
        Returns True if coords is a set of coordinates inside this Level.
        
        Returns False otherwise.
        """
        
        legality = True
        
        for i in range(len(self.dimensions)):
            if coords[i] < 0:
                legality = False
            if coords[i] >= self.dimensions[i]:
                legality = False
        
        return legality
    
    def moveDude(self, movedDude, moveCoords):
        self.__delCharacterFromMap(movedDude.coords, self.__DUDE_HEIGHT)
        self.dudeLayer.moveObject(movedDude, moveCoords)
        self.__addCharacterToMap(movedDude.getCurGlyph(), movedDude.coords, self.__DUDE_HEIGHT)

    def createMonster(self, mon_name, coords):
        """
        Create a monster of the name mon_name.

        If the coordinates are already occupied, raise an OccupiedLocationError.
        """
        
        if not self.isEmpty(coords):
            raise ValueError(
                "%s in which monster %s was created is a wall!"
                % (coords, mon_name))
        if coords in self.dudeLayer:
            raise exc.OccupiedLocationError(
                "Location %s where %s was created is already occupied!"
                % (coords, mon_name))

        new_mon = self.definition.monster_factory.create(mon_name)
        self.addDude(new_mon, coords, True)

    def makeNoise(self, message, center):
        """
        Add a message to the queue provided a certain square is in player FOV.

        message - a string containing the message to be displayed.
        center - the square which must be in FOV for the message to be displayed.
        """
        
        self.getPlayer().resetFOV()
        if center in self.getPlayer().fov:
            self.messages.append(message)

        return
    
    def resetQueue(self):
        """
        Reset the Level's internal queue of dudes (in the order in which they
        are acting).
        
        The following restrictions are in place here:
        1. The player, if he is moving, always moves first.
        2. The monsters move in a consistent order.
        3. After the monsters move, all events occur.
        """

# The first dude in the queue is the player, but there is no real necessity
# for this - it is a design decision.  The first object in the queue, however,
# is an instance of the LevelTick class, which is not a dude.  Rather,
# the LevelTick instance updates things in the Level which should only be
# updated once per turn.  Currently, this LevelTick instance is a piece of
# state local to the Level it updates.

        q = queue.PriorityQueue()
        for e in self.events:
            q.put(e, 0)
        q.put(self.player, 0)
        for p in self.dudeLayer:
            if not p.isPlayer():
                q.put(p, 0)

        self.__queue = q

    def addEvent(self, event, execution_time):
        """
        Add an event to the level.
        """
        self.events.append(event)
        if self.__queue is not None:
            self.__queue.put(event, self.time + execution_time)

    def next(self):
        """
        Make the next dude in the level's queue take an action.  Note
        that the dude may take any number of actions that don't take up
        its turn without this method returning.
        """
        
        if (self.__queue is None) or (self.__queue.isEmpty()):
            self.resetQueue()
        self.time += self.__queue.priority_interval()
        next_actor = self.__queue.get()

# The act() method returns the speed of the action, the number of ticks until
# the actor gets to move again.  (If the number of ticks is 0, things get weird,
# so this method just asks for another action instead of going through the
# queue.
        actor_ticks = 0
        while actor_ticks == 0 and next_actor.exists():
            actor_ticks = next_actor.act()

        if next_actor.exists():
            self.__queue.put(next_actor, self.time + actor_ticks)

        return

class Layer(list):
    """
    A Layer is a collection of FixedObjects, all on the same level.
    
    There can be a Trap Layer, a Dude Layer, etcetera.
    Note that the Layer dict's keys are the coords of said objects.
    Layers are intended for collections in which not every square is full.
    
    Note that the dudes should not normally be directly added to the DudeLayer;
    they should be added through a Level instead.
    """
    
    def __init__(self, dimensions):
        """
        Supply a tuple for dimensions.
        """
        
        #if initThing is None:
        list.__init__(self)
        #else:
        #    dict.__init__(self, initThing)
            
        self.dimensions = dimensions
        self.coordinateDict = {}
    
    def __getitem__(self, key):
        """Works with dictionary key as well."""
        try:
            k = key[0]
        except TypeError:
            # key is not a sequence; assumed to be a list key
            return list.__getitem__(self, key)
        else:
            # key is a sequence, assumed to be a coord key
            return self.coordinateDict[key]
    
    def __delitem__(self, key):
        """Deletes from dictionary as well."""
        try:
            k = key[0]
        except TypeError:
            # This will screw up silently if coords is wrong!
            del self.coordinateDict[self[key].coords]
            list.__delitem__(self, key)
        else:
            list.__delitem__(self, self.index(self[key]))
            del self.coordinateDict[key]

    def __contains__(self, item):
        """Returns true with an item in this Layer or coordinates of one."""
        try:
            item[0]
        except TypeError:
            return list.__contains__(self, item)
        else:
            return item in self.coordinateDict
    
    def __addCoords(self, item):
        """
        Add the coordinates of an item to the layer's coord dict.
        """
        self.coordinateDict[item.coords] = item
    
    def __changeCoords(self, item, newCoords):
        """
        Change the coordinates of an item in the coord dict to newCoords.
        
        changeCoords changes ONLY the coordinates in this Layer's coordinate
        dict, and, in fact, WILL NOT WORK if the FixedObject's coordinates in
        its coords attribute differ from its coordinates inside the coordinate
        dict of this layer.
        """
        del self.coordinateDict[item.getCoords()]
        self.coordinateDict[newCoords] = item
    
    def moveObject(self, movedDude, moveCoords):
        """
        Move an object from its current coordinates to moveCoords.
        
        This method changes both the coords inside the FixedObject and the
        coords inside this Layer's internal map.
        """
        dudeOriginalCoords = movedDude.getCoords()
        if dudeOriginalCoords != moveCoords:
            self.__changeCoords(movedDude, moveCoords)
            movedDude.setCoords(moveCoords)

    def getArray(self):
        array = arrays.empty_str_array(self.dimensions)
        for item in self:
            array[item.coords] = item.getCurGlyph()
        return array
    
    def append(self, item):
        """Adds to dictionary as well."""
        list.append(self, item)
        self.__addCoords(item)
        
    def extend(self, item):
        """Adds to dictionary as well."""
        for i in item:
            self.append(i)

class DudeLayer(Layer):
    """
    Just like a Layer, except that it has a nice, convenient queue.
    """
    
    def __init__(self, player = None, *args, **kwds):
        Layer.__init__(self, *args, **kwds)
        self.moveQueue = []
        self.player = player
    
    def remove(self, removed):
        """
        Remove something from this layer.
        """
        
        removed.setCurrentLevel(None)
        # These lines is horribly inefficient; there's got to be a better way.
        del self[self.index(removed)]

class FloorDefinition(object):
    """
    A floor's definition, which defines how it is randomly created.
    """

    def __init__(self, floor, rarities, monster_factory):
        """
        rarities - a sequence of tuples of the form (rarity, monster_name),
            which determine how common each type of monster is on this floor.
            Note that if a monster does not appear on this floor, it is not
            necessary to include it in the rarity sequence.
        monster_factory - a monster factory.
        """
        self.floor = floor
        self.rarities = list(rarities)
        self.monster_factory = monster_factory
        self.total = sum([i for i,j in self.rarities])

    def getRandomMonster(self):
        """
        Return a random monster created on this floor.
        """
        if self.total == 0 or len(self.rarities) == 0:
            return self.monster_factory.getBuggyMonster()

        random_number = rng.randInt(0, self.total - 1)
        for r in self.rarities:
            random_number -= r[0]
            if random_number < 0:
                return self.monster_factory.create(r[1])

def empty_dungeon(dimensions):
    """
    Return an empty dungeon with the dimensions specified.
    """

    return arrays.empty_str_array(dimensions)

def empty_elements(dimensions):
    """
    Return an empty container of terrain elements with the dimensions given.
    """
    
    return symbol.glyphMap(dimensions)

def make_sight_map(dungeon):
    """
    Returns a TCOD sight map of the dungeon given.

    dungeon - a dungeon array.
    dimensions - the dime
    """
    
    dimensions = dungeon.shape
    smap = tcod.map_new(dimensions[0], dimensions[1])
    for i in range(dimensions[0]):
        for j in range(dimensions[1]):
            tcod.map_set_properties(smap, i, j, dungeon[i, j] in OPEN_GLYPHS, False)

    return smap
