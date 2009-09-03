"""
Deals with file input, output, and parsing.
"""

# This file, before commit 67d519e, contained (non-working) code to create a
# predesigned level from a file.

from __future__ import with_statement

import cPickle
import os

import dude
import level
import symbol
import coordinates
import exc
import log

def save_game(player, floor):
    """
    Save the game state of a player traveling upstairs.

    player - the player to be saved.
    floor - the floor to which the player is traveling.
    """

    with open("%s.sav" % player.name, 'w') as save_file:
        cPickle.dump((player, floor), save_file, 0)

def restore_save(filename):
    """
    Restore the game state of a player traveling upstairs.

    Returns: The tuple (player, floor), where player is the player traveling
        upstairs and floor is said player's new floor.
    """

    with open(filename, 'r') as save_file:
        return cPickle.load(save_file)

def getFile(filename):
    """
    Return a list containing the lines of a file, stripping newline characters.
    """
    
    linelist = []
    
    with open(filename, 'r') as configfile:
        
        for line in configfile:
            if line[0] != '~':
                if '~' in line:
                    linelist.append(line[:line.index('~')])
                else:
                    linelist.append(line[:-1] if line[-1] == '\n' else line)
            
        #linelist = configfile.readlines()
    
    #linelist = [(line[:-1] if line[-1] == '\n' else line) for line in linelist]
    return linelist

def getMonsterFactory(linelist, initline = 0):
    """
    Returns a monster factory with the monsters detailed in the lines given.
    """
    
    curline = initline
    retFactory = dude.MonsterFactory()
    
    while 1: #continue loop until out of tags
        try:
            curline = findTag(linelist, "<MONSTER>", curline)
        except exc.TagLocationError:
            break
        else:
            new_monster = getMonster(linelist, curline)
            if "bug_monster" in new_monster.tags:
                retFactory.setBuggyMonster(new_monster)
            else:
                retFactory.append(getMonster(linelist, curline))
            curline += 1
    
    return retFactory

def getMonster(linelist, initline = 0):
    """
    Given the starting line, translate a text-file description into a Monster.
    """
    
    if linelist[initline] != "<MONSTER>":
        raise ValueError("Monster data begins with %s, not <MONSTER>." % linelist[initline])
    
    lastline = findTag(linelist, "[ENDSEC]", initline)
    try:
        tagline = findTag(linelist, "[TAG]", initline, lastline)
    except exc.TagLocationError:
        tags = []
    else:
        endline = findTag(linelist, "[END]", tagline, lastline)
        tags = linelist[tagline + 1:endline]
    
    attrDict = labelDict(linelist, initline + 1, lastline)
    
    return dude.Monster(attrDict["name"],
                        None, 
                        symbol.Glyph(attrDict["glyph"], (int(attrDict["r"]), int(attrDict["g"]), int(attrDict["b"]))),
                        attrDict["ai"],
                        int(attrDict["speed"]),
                        int(attrDict["hp"]),
                        tags,
                        int(attrDict["atk"]),
                        int(attrDict["def"]),
                        int(attrDict["level"]),
                        attrDict["spec"],
                        int(attrDict["specfreq"]),
                        None
                        )

def getFloorDefinitions(monster_factory, linelist, initline = 0):
    """
    Return a dictionary containing the floor definitions of each floor.

    The dictionary is of the form {floor_number:floor_definition, etc.}
    """
    curline = initline
    floor_dict = {}
    while 1: # continue loop until out of tags
        try:
            curline = findTag(linelist, "<LEVEL>", curline)
        except exc.TagLocationError:
            break
        else:
            new_floor_def = getFloorDef(monster_factory, linelist, curline)
            floor_dict[new_floor_def.floor] = new_floor_def
        curline += 1

    return floor_dict

def getFloorDef(monster_factory, linelist, initline = 0):
    """
    Translate a given text description of a floor into a FloorDefinition.
    """
    
    if linelist[initline] != "<LEVEL>":
        raise ValueError("Floor data begins with %s, not <LEVEL>." % linelist[initline])
    
    lastline = findTag(linelist, "[ENDSEC]", initline)
    try:
        monstersline = findTag(linelist, "[MONSTERS]", initline, lastline)
    except exc.TagLocationError:
        raise exc.InvalidDataError("No \"[MONSTERS]\" line found in levels.dat between %d and %d" % (initline, lastline))
    else:
        endline = findTag(linelist, "[END]", monstersline, lastline)
        raritylist = [(int(j), i) for (i, j) in labelDict(linelist, monstersline, endline, ':').items()]
    
    attrDict = labelDict(linelist, initline + 1, lastline)

    return level.FloorDefinition(int(attrDict["floor"]),
                                 raritylist,
                                 monster_factory)
    
    return dude.Monster(attrDict["name"],
                        None, 
                        symbol.Glyph(attrDict["glyph"], (int(attrDict["r"]), int(attrDict["g"]), int(attrDict["b"]))),
                        attrDict["ai"],
                        int(attrDict["speed"]),
                        int(attrDict["hp"]),
                        tags,
                        int(attrDict["atk"]),
                        int(attrDict["def"]),
                        int(attrDict["level"]),
                        attrDict["spec"],
                        int(attrDict["specfreq"]),
                        None
                        )

def findTag(linelist, tag, startLine = 0, dontGoPast = None):
    """
    Find the first line that contains only the tag given.  Returns its index.
    
    findTag will check every line from startLine to but not including
    dontGoPast.  findTag raises a TagLocationError if the tag isn't there.
    """
    
    for i in range(startLine, dontGoPast if dontGoPast is not None else len(linelist)):
        if tag == linelist[i]:
            return i
    
    raise exc.TagLocationError("%s not found in list provided; try loosening range." % tag)

def labelDict(linelist, startLine = 0, endLine = None, separator = '='):
    """
    Given a list of strings, returns a dict connecting identifiers with codes.
    
    More specifically, the text on the left side of the first use of the
    separator is used as a key, and the text on the right side is used as the
    value.  This is done for each line from startLine up to but not including
    endLine.
    """
    
    retDict = {}
    
    for line in linelist[startLine:endLine]:
        separatorIndex = line.find(separator)
        if separatorIndex != -1:
            dictTuple = line.split(separator, 2)
            retDict[dictTuple[0]] = dictTuple[1]
    
    return retDict
