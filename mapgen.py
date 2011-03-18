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
import fileio

NUM_SECTORS_X = 4
NUM_SECTORS_Y = 3
NUMBER_OF_MONSTERS = 0
MAX_SIZE_X = 120
MAX_SIZE_Y = 120
SECTOR_SIZE_X = 12
SECTOR_SIZE_Y = 12
NW_CORNER_X = 10
NW_CORNER_Y = 10
MIN_ROOM_SIZE = 3
MAX_ROOM_SIZE = 8

class st:
    """
    A glorified enum of sector types.
    """
    (
    EMPTY,
    ROOM,
    DOUBLE_ROOM,
    CORRIDOR,
    ) = range(4)

def randomDungeon():
    """
    Gets a random dungeon, using a very simple room/corridor model.
    
    The room/corridor model used is similar to that of Rogue; the map is
    divided into nine sectors, each of which is randomly called a room,
    a corridor, or empty.  Once this is done, rooms and corridors are connected
    to adjacent rooms and corridors.
    
    This is coded terribly because it will be replaced someday.
    """
    
    map_dimensions = (MAX_SIZE_X, MAX_SIZE_Y)
    map_nwcorner = (NW_CORNER_X, NW_CORNER_Y)
    sector_size = (SECTOR_SIZE_X, SECTOR_SIZE_Y)
    sector_list = [(x, y) for x in range(NUM_SECTORS_X) 
                          for y in range(NUM_SECTORS_Y)]
    sector_nwcorners = {}
    for x in range(NUM_SECTORS_X):
        for y in range(NUM_SECTORS_Y):
            sector_nwcorners[(x, y)] = (
                map_nwcorner[0] + sector_size[0] * x,
                map_nwcorner[1] + sector_size[1] * y
                )
                
    sector_types = {}
    for x in range(NUM_SECTORS_X):
        for y in range(NUM_SECTORS_Y):
            percent = rng.randInt(1, 100)
            if percent <= 25:
                sector_types[(x, y)] = st.ROOM
            elif percent <= 60:
                sector_types[(x, y)] = st.DOUBLE_ROOM
            elif percent <= 75:
                sector_types[(x, y)] = st.CORRIDOR
            else:
                sector_types[(x, y)] = st.EMPTY
    
    room_nwcoords = {}
    room_secoords = {}
    
    for sector_coords in sector_types.keys():
        sector_nw = sector_nwcorners[sector_coords]
        sector_se = (sector_nw[0] + sector_size[0] - 1,
                     sector_nw[1] + sector_size[1] - 1)

        if sector_types[sector_coords] in (st.ROOM, st.DOUBLE_ROOM):
            (room_nwcoords[sector_coords], room_secoords[sector_coords]) \
                = choose_room_corners(sector_nw, sector_se)
                    
        elif sector_types[sector_coords] == st.CORRIDOR:
            # A corridor is currently implemented as just a 1-space room.
            corridor_coords = (rng.randInt(sector_nw[0], sector_se[0]),
                rng.randInt(sector_nw[1], sector_se[1]))

            room_nwcoords[sector_coords] = corridor_coords
            room_secoords[sector_coords] = corridor_coords
    
    # Check whether everywhere is accessible; if not, do a redo.
    sector_is_accessible = {}
    for x in range(NUM_SECTORS_X):
        for y in range(NUM_SECTORS_Y):
            sector_is_accessible[(x, y)] = False
    
    for coord in sector_list:

        if True not in sector_is_accessible.values() \
            and sector_types[coord] != 0:

            sector_is_accessible[coord] = True
        
        if sector_is_accessible[coord] == True \
            and sector_types[coord] != st.EMPTY:

            for coord_adjustment in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                adjacent_coord = coordinates.add(coord, coord_adjustment)
                if (adjacent_coord[0] >= 0 and
                    adjacent_coord[0] < NUM_SECTORS_X and
                    adjacent_coord[1] >= 0 and
                    adjacent_coord[1] < NUM_SECTORS_Y):
                    
                    sector_is_accessible[adjacent_coord] = True
    
    for accessible in sector_is_accessible.items():
        if sector_types[accessible[0]] != 0 and not accessible[1]:
            # Oops.  Give up and try again.
            return randomDungeon()
    
    entrance_sector = rng.choice([coords for coords in sector_types.keys() 
                                 if sector_types[coords] in 
                                 (st.ROOM, st.DOUBLE_ROOM)])
    exit_sector = rng.choice([coords for coords in sector_types.keys() 
                              if sector_types[coords] in
                              (st.ROOM, st.DOUBLE_ROOM)])
    entrance_coords = rng.randomPointInRect(room_nwcoords[entrance_sector], 
                                            room_secoords[entrance_sector])
    exit_coords = rng.randomPointInRect(room_nwcoords[exit_sector], 
                                        room_secoords[exit_sector])
    
    ret_dungeon = level.empty_dungeon(map_dimensions)
    
    for coord in sector_list:
        if sector_types[coord] != st.EMPTY:
            if sector_types[coord] == st.CORRIDOR:
                fill_glyph = level.CORRIDOR_GLYPH
            else:
                fill_glyph = level.ROOM_INTERIOR_GLYPH

            arrays.fill_rect(ret_dungeon, room_nwcoords[coord], 
                room_secoords[coord], fill_glyph)
            
# If there is another room to the south or east, make a corridor from this room
# to it.
            for coord_adjustment in ((1, 0), (0, 1)):
                adjacent_coord = coordinates.add(coord, coord_adjustment)
                if (adjacent_coord[0] < NUM_SECTORS_X 
                    and adjacent_coord[1] < NUM_SECTORS_Y
                    and sector_types[adjacent_coord] != 0):

                    make_corridor(ret_dungeon,
                        rng.randomPointInRect(room_nwcoords[coord], 
                                              room_secoords[coord]),
                        rng.randomPointInRect(room_nwcoords[adjacent_coord], 
                                              room_secoords[adjacent_coord]))

# If the room type is DOUBLE_ROOM, bolt on a second room to the first.
# This room can overflow! That is intentional.
            if sector_types[coord] == st.DOUBLE_ROOM:
                max_second_se = (room_secoords[coord][0] + MIN_ROOM_SIZE,
                                 room_secoords[coord][1] + MIN_ROOM_SIZE)
                (second_nw, second_se) = choose_room_corners(
                    room_nwcoords[coord], max_second_se)

                arrays.fill_rect(ret_dungeon, second_nw, second_se, 
                    level.ROOM_INTERIOR_GLYPH)
    
    ret_dungeon[entrance_coords] = level.UPSTAIRS_GLYPH
    ret_dungeon[exit_coords] = level.DOWNSTAIRS_GLYPH
    
    return ret_dungeon

def choose_room_corners(possible_nw, possible_se):
    """
    Generate possible northwest and southeast corners for a room.

    possible_nw: the upper-left-most possible square in which the room can be.
    possible_se: the lower-right-most possible square in which the room can be.
    """
    if (possible_nw[0] + MIN_ROOM_SIZE > possible_se[0]
        or possible_nw[1] + MIN_ROOM_SIZE > possible_se[1]):
        raise ValueError("Not enough room for a room in %s, %s."
            % (possible_nw, possible_se))
    while True:
        room_nw = (rng.randInt(possible_nw[0], possible_se[0]),
                    rng.randInt(possible_nw[1], possible_se[1]))
        room_se = (room_nw[0] + rng.randInt(MIN_ROOM_SIZE, MAX_ROOM_SIZE),
                  (room_nw[1] + rng.randInt(MIN_ROOM_SIZE, MAX_ROOM_SIZE)))
            
        # check validity of room dimensions
        if room_se[0] <= possible_se[0] and room_se[1] <= possible_se[1]:
            return (room_nw, room_se)

def make_corridor(dungeon, start_coords, end_coords):
    """
    Modifies the dungeon given to construct a corridor.
    """
    
    # Identify the dimension over which most of the travel is happening, and
    # allow the rest of the code to work in a dimension-agnostic manner.
    if (abs(end_coords[0] - start_coords[0]) > 
        abs(end_coords[1] - start_coords[1])):
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
    kink_major_coordinate = rng.randInt(first_coords[major_dimension], 
                                        last_coords[major_dimension])
    
    for major_coordinate in range(first_coords[major_dimension], 
                                  kink_major_coordinate + 1):
        current_coords = [0, 0]
        current_coords[major_dimension] = major_coordinate
        current_coords[minor_dimension] = first_coords[minor_dimension]
        current_coords = tuple(current_coords)
        if dungeon[current_coords] == config.TRANSPARENT_GLYPH:
            dungeon[current_coords] = level.CORRIDOR_GLYPH
    
    if first_coords[minor_dimension] <= last_coords[minor_dimension]:
        minor_coordinate_range = range(first_coords[minor_dimension], 
                                       last_coords[minor_dimension] + 1)
    else:
        minor_coordinate_range = range(last_coords[minor_dimension], 
                                       first_coords[minor_dimension] + 1)
    
    for minor_coordinate in minor_coordinate_range:
        current_coords = [0, 0]
        current_coords[major_dimension] = kink_major_coordinate
        current_coords[minor_dimension] = minor_coordinate
        current_coords = tuple(current_coords)
        if dungeon[current_coords] == config.TRANSPARENT_GLYPH:
            dungeon[current_coords] = level.CORRIDOR_GLYPH
    
    for major_coordinate in range(kink_major_coordinate, 
                                  last_coords[major_dimension] + 1):
        current_coords = [0, 0]
        current_coords[major_dimension] = major_coordinate
        current_coords[minor_dimension] = last_coords[minor_dimension]
        current_coords = tuple(current_coords)
        if dungeon[current_coords] == config.TRANSPARENT_GLYPH:
            dungeon[current_coords] = level.CORRIDOR_GLYPH

def populate_level(pop_level, floor_def):
    """
    Populate a given level with monsters.
    """

    level_nwcorner = (0, 0)
    level_secorner = [dim - 1 for dim in pop_level.dimensions]

    for i in range(NUMBER_OF_MONSTERS):
        monster_to_be_made = floor_def.getRandomMonster()
        monster_has_been_created = False
        while not monster_has_been_created:
            monster_coords = rng.randomPointInRect(
                level_nwcorner, level_secorner)
            if (pop_level.dungeonGlyph(monster_coords) in 
                level.PASSABLE_TERRAIN
                and monster_coords not in pop_level.dudeLayer):
                
                pop_level.addDude(monster_to_be_made, monster_coords, False)
                monster_has_been_created = True

def randomLevel(floor_def, player):
    """
    If no player is supplied, the player slot is just left empty.
    """

    if floor_def.floor == 8:
        return bossLevel(floor_def.monster_factory, player)
    
    dungeon = randomDungeon()
    ret_level = constructLevelFromDungeon(dungeon, floor_def, player)
    
    populate_level(ret_level, floor_def)

    return ret_level

def bossLevel(monster_factory, player):
    
    dungeon = fileio.getCustomDungeon("final.map")
    floor_def = level.FloorDefinition(8, (), monster_factory)
    ret_level = constructLevelFromDungeon(dungeon, floor_def, player)
    return ret_level

def constructLevelFromDungeon(dungeon, floor_def, player):
    """
    Returns an unpopulated but playable level using the dungeon given.
    """

    elements = level.empty_elements(dungeon.shape)
    
    entrance_coords = arrays.index(level.DOWNSTAIRS_GLYPH, dungeon)
    # Currently, the > glyph is not used in the game, as downward travel cannot
    # happen.
    # elements[entrance_coords] = level.DOWNSTAIRS_GLYPH
    dungeon[entrance_coords] = level.ROOM_INTERIOR_GLYPH
    
    exit_coords = arrays.find(level.UPSTAIRS_GLYPH, dungeon)
    if exit_coords is not None:
        elements[exit_coords] = level.UPSTAIRS_GLYPH
        dungeon[exit_coords] = level.ROOM_INTERIOR_GLYPH
    
    ret_level = level.Level(dungeon.shape, floor_def.floor, None, elements, 
        dungeon, floor_def)
    
    if player is not None:
        ret_level.addPlayer(player, entrance_coords)

    return ret_level

