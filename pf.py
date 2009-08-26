import collections

import coordinates
import exc

"""
Pathfinding tools.

Note that a "path" is a list of the form:
[source, a, b, c, ... destination]
where each element is adjacent to the element before.
"""

def find_shortest_path(level_, source, destination, destination_must_be_clear = False):
    """
    Find the shortest path between two coordinates on the level.
    
    This algorithm does take into account monsters between two points.
    However, monsters on the squares source and destination are ignored.

    level_ - the level being searched.
    source - the beginning of the path.
    destination - the end of the path.
    destination_must_be_clear - True if the pathfinding should fail if the
        destination has a monster on it.  False otherwise.

    Returns: a list containing the shortest path between the source and the 
        destination, or the empty list, if no such path exists.
    """
    
    if destination_must_be_clear:
        def adjacent_squares_function(square):
            passable_coords = level_.immediately_accessible_squares(square)
            no_monster_coords = [i for i in passable_coords if 
                ((i not in level_.dudeLayer)
                 or (i == source))]
            return no_monster_coords
    else:
        def adjacent_squares_function(square):
            passable_coords = level_.immediately_accessible_squares(square)
            no_monster_coords = [i for i in passable_coords if 
                ((i not in level_.dudeLayer)
                 or (i in (source, destination)))]
            return no_monster_coords
    
    try:
        return _find_shortest_path(level_.dimensions, adjacent_squares_function, source, destination)
    except exc.PathfindingError:
        return []

def _find_shortest_path(dimensions, adjacent_squares_function, source, destination):
    """
    Find the shortest path between two coordinates on an grid.

    dimensions - the dimensions of the grid.
    adjacent_squares_function - a function of the form:
        adjacent_squares_function(square): return an iterable of the
        squares adjacent to square.
    source - the beginning of the path.
    destination - the end of the path.

    Returns: a list containing the shortest path between the source and the
        destination.
    """
    
    predecessors = _breadth_first_search_predecessors(dimensions, adjacent_squares_function, source, destination)
    if destination not in predecessors:
        raise PathfindingError("No path exists between %s and %s!"
            % (source, destination))
    else:
        path = []
        current_square = destination
        while predecessors[current_square] is not None:
            path.insert(0, current_square)
            current_square = predecessors[current_square]
        path.insert(0, source)

    return path

def _breadth_first_search_predecessors(dimensions, adjacent_squares_function, source, destination = None):
    """
    Returns a path from source to each square in the graph.
    
    dimensions - the dimensions of the graph to be searched.
    adjacent_squares_function - a function of the form:
        adjacent_squares_function(square): return an iterable of the
        squares adjacent to square.
    source - the first square in each path.
    destination - if destination != None, then the search is halted as soon as
        its coordinates are found.  If destination is then not found at all, a
        PathfindingError is thrown.

    Returns: a dict whose keys are reachable coordinates from source, and whose
        values are the previous coordinates in the path from the source to that
        set of coordinates.
        Note that source is a key in this dict, whose value is None.
    """

# Those coordinates whose neighbors' paths have been determined.
    settled = set() 

# Those coordinates whose paths have been determined, but whose neighbors'
# paths have not.
    horizon = set()
    horizon.add(source)

# The dictionary to be returned.
    predecessors = dict()
    predecessors[source] = None
    destination_is_none = destination is None

    while destination_is_none or destination not in settled:
        
        if len(horizon) == 0:
            if destination_is_none:
                break
            else:
                raise exc.PathfindingError("%s, the destination, is unreachable from %s, the source."
                    % (destination, source))

        new_horizon = set()
        for coords in horizon:
            adjacent_coords = adjacent_squares_function(coords)
# This line may be changed if I wish to add a chance that a coord in new_horizon is chosen.
            adjacent_coords = [c for c in adjacent_coords if (c not in settled and c not in horizon and c not in new_horizon)]
            for adjacent in adjacent_coords:
                new_horizon.add(adjacent)
                predecessors[adjacent] = coords
        settled.update(horizon)
        horizon = new_horizon
    
    return predecessors
