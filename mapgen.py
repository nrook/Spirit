"""
Contains various dungeon generation functions.
"""

import arrays
import rng
import coordinates
import level
import log
import dude
import config

def randomDungeon():
    """
    Gets a random dungeon, using a very simple room/corridor model.
    
    The room/corridor model used is similar to that of Rogue; the map is
    divided into nine sectors, each of which is randomly called a room,
    a corridor, or empty.  Once this is done, rooms and corridors are connected
    to adjacent rooms and corridors.
    
    This is coded terribly because it will be replaced someday.
    """
    
    map_dimensions = (60, 60)
    map_nwcorner = (10, 10)
    sector_size = (12, 12)
    sector_nwcorners = {}
    for x in range(0, 3):
        for y in range(0, 3):
            sector_nwcorners[(x, y)] = (
                map_nwcorner[0] + sector_size[0] * x,
                map_nwcorner[1] + sector_size[1] * y
                )
                
    sector_types = {}
    for x in range(0, 3):
        for y in range(0, 3):
            percent = rng.randInt(1, 100)
            if percent <= 60:
                sector_types[(x, y)] = 1 # it's a room!
            elif percent <= 75:
                sector_types[(x, y)] = 2 # it's a corridor!
            else:
                sector_types[(x, y)] = 0 # it's empty!
    
    room_nwcoords = {}
    room_secoords = {}
    
    for sector_coords in sector_types.keys():
        if sector_types[sector_coords] == 1:
            room_created = False
            sector_nw = sector_nwcorners[sector_coords]
            sector_se = (sector_nw[0] + sector_size[0] - 1, sector_nw[1] + sector_size[1] - 1)
            while not room_created:
                room_nw = (rng.randInt(sector_nw[0], sector_se[0]),
                           rng.randInt(sector_nw[1], sector_se[1]))
                room_se = (room_nw[0] + rng.randInt(3, 8),
                           room_nw[1] + rng.randInt(3, 8))
            
                # check validity of room dimensions
                if room_se[0] <= sector_se[0] and room_se[1] <= sector_se[1]:
                    room_nwcoords[sector_coords] = room_nw
                    room_secoords[sector_coords] = room_se
                    room_created = True
                    
        elif sector_types[sector_coords] == 2:
            # A corridor is currently implemented as just a 1-space room.
            corridor_coords = (rng.randInt(sector_nwcorners[sector_coords][0],
                                           sector_nwcorners[sector_coords][0] + sector_size[0] - 1,),
                               rng.randInt(sector_nwcorners[sector_coords][1],
                                           sector_nwcorners[sector_coords][1] + sector_size[1] - 1,))
            room_nwcoords[sector_coords] = corridor_coords
            room_secoords[sector_coords] = corridor_coords
    
    # Check whether everywhere is accessible; if not, do a redo.
    sector_is_accessible = {}
    for x in range(3):
        for y in range(3):
            sector_is_accessible[(x, y)] = False
    
    for coord in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)):
        if True not in sector_is_accessible.values() and sector_types[coord] != 0:
            sector_is_accessible[coord] = True
        
        if sector_is_accessible[coord] == True and sector_types[coord] != 0:
            for coord_adjustment in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                adjacent_coord = coordinates.add(coord, coord_adjustment)
                if (adjacent_coord[0] >= 0 and
                    adjacent_coord[0] < 3 and
                    adjacent_coord[1] >= 0 and
                    adjacent_coord[1] < 3):
                    
                    sector_is_accessible[adjacent_coord] = True
    
    for accessible in sector_is_accessible.items():
        if sector_types[accessible[0]] != 0 and not accessible[1]:
            # Oops.  Give up and try again.
            return randomDungeon()
    
    entrance_sector = rng.choice([coords for coords in sector_types.keys() if sector_types[coords] == 1])
    exit_sector = rng.choice([coords for coords in sector_types.keys() if sector_types[coords] == 1])
    entrance_coords = rng.randomPointInRect(room_nwcoords[entrance_sector], room_secoords[entrance_sector])
    exit_coords = rng.randomPointInRect(room_nwcoords[exit_sector], room_secoords[exit_sector])
    
    ret_dungeon = level.empty_dungeon(map_dimensions)
    
    for coord in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)):
        if sector_types[coord] != 0:
            for x in range(room_nwcoords[coord][0], room_secoords[coord][0] + 1):
                for y in range(room_nwcoords[coord][1], room_secoords[coord][1] + 1):
                    if sector_types[coord] == 1:
                        ret_dungeon[(x, y)] = level.ROOM_INTERIOR_GLYPH
                    else:
                        ret_dungeon[(x, y)] = level.CORRIDOR_GLYPH
            
            for coord_adjustment in ((1, 0), (0, 1)):
                adjacent_coord = coordinates.add(coord, coord_adjustment)
                if (adjacent_coord[0] < 3 and adjacent_coord[1] < 3 and sector_types[adjacent_coord] != 0):
                    make_corridor(ret_dungeon,
                        rng.randomPointInRect(room_nwcoords[coord], room_secoords[coord]),
                        rng.randomPointInRect(room_nwcoords[adjacent_coord], room_secoords[adjacent_coord]))
    
    ret_dungeon[entrance_coords] = level.UPSTAIRS_GLYPH
    ret_dungeon[exit_coords] = level.DOWNSTAIRS_GLYPH
    
    return ret_dungeon

def make_corridor(dungeon, start_coords, end_coords):
    """
    Modifies the dungeon given to construct a corridor.
    """
    
    # Identify the dimension over which most of the travel is happening, and
    # allow the rest of the code to work in a dimension-agnostic manner.
    if abs(end_coords[0] - start_coords[0]) > abs(end_coords[1] - start_coords[1]):
        major_dimension = 0
        minor_dimension = 1
    else:
        major_dimension = 1
        minor_dimension = 0
    
    if end_coords[major_dimension] - start_coords[major_dimension] >= 0:
        first_coords = start_coords
        last_coords = end_coords
    else:
        first_coords = end_coords
        last_coords = start_coords
    
    # The kink is the major dimension coordinate at which the corridor starts
    # moving on the minor dimension, not the major dimension.
    kink_major_coordinate = rng.randInt(first_coords[major_dimension], last_coords[major_dimension])
    
    for major_coordinate in range(first_coords[major_dimension], kink_major_coordinate + 1):
        current_coords = [0, 0]
        current_coords[major_dimension] = major_coordinate
        current_coords[minor_dimension] = first_coords[minor_dimension]
        current_coords = tuple(current_coords)
        if dungeon[current_coords] == config.TRANSPARENT_GLYPH:
            dungeon[current_coords] = level.CORRIDOR_GLYPH
    
    if first_coords[minor_dimension] <= last_coords[minor_dimension]:
        minor_coordinate_range = range(first_coords[minor_dimension], last_coords[minor_dimension] + 1)
    else:
        minor_coordinate_range = range(last_coords[minor_dimension], first_coords[minor_dimension] + 1)
    
    for minor_coordinate in minor_coordinate_range:
        current_coords = [0, 0]
        current_coords[major_dimension] = kink_major_coordinate
        current_coords[minor_dimension] = minor_coordinate
        current_coords = tuple(current_coords)
        if dungeon[current_coords] == config.TRANSPARENT_GLYPH:
            dungeon[current_coords] = level.CORRIDOR_GLYPH
    
    for major_coordinate in range(kink_major_coordinate, last_coords[major_dimension] + 1):
        current_coords = [0, 0]
        current_coords[major_dimension] = major_coordinate
        current_coords[minor_dimension] = last_coords[minor_dimension]
        current_coords = tuple(current_coords)
        if dungeon[current_coords] == config.TRANSPARENT_GLYPH:
            dungeon[current_coords] = level.CORRIDOR_GLYPH

def populate_level(pop_level, monster_fact, dlvl):
    """
    Populate a given level with monsters.
    """

    NUMBER_OF_MONSTERS = 18
    
    level_nwcorner = (0, 0)
    level_secorner = [dim - 1 for dim in pop_level.dimensions]

    for i in range(NUMBER_OF_MONSTERS):
        monster_to_be_made = monster_fact.getRandomMonster(dlvl)
        monster_has_been_created = False
        while not monster_has_been_created:
            monster_coords = rng.randomPointInRect(level_nwcorner, level_secorner)
            if pop_level.dungeonGlyph(monster_coords) in level.PASSABLE_TERRAIN and \
                monster_coords not in pop_level.dudeLayer:
                
                pop_level.addDude(monster_to_be_made, monster_coords, False)
                monster_has_been_created = True

def randomLevel(floor, player, monster_fact):
    """
    If no player is supplied, the player slot is just left empty.
    """
    
    dungeon = randomDungeon()
    elements = level.empty_elements(dungeon.shape)
    
    entrance_coords = arrays.index(level.DOWNSTAIRS_GLYPH, dungeon)
    # Currently, the > glyph is not used in the game, as downward travel cannot
    # happen.
    # elements[entrance_coords] = level.DOWNSTAIRS_GLYPH
    dungeon[entrance_coords] = level.ROOM_INTERIOR_GLYPH
    
    exit_coords = arrays.index(level.UPSTAIRS_GLYPH, dungeon)
    elements[exit_coords] = level.UPSTAIRS_GLYPH
    dungeon[exit_coords] = level.ROOM_INTERIOR_GLYPH
    
    ret_level = level.Level(dungeon.shape, floor, None, elements, dungeon, monster_fact)
    
    if player is not None:
        ret_level.addPlayer(player, entrance_coords)
    
    populate_level(ret_level, monster_fact, floor)

    return ret_level
    
