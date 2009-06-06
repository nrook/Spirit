"""
Deals with file input, output, and parsing.
"""

from __future__ import with_statement

import dude
import level
import symbol
import coordinates
import log
import os

def restoreSave(filename, monster_factory, delete_save):
    """
    Converts a save file into actual game data, and returns a tuple with it.
    
    Exactly what is in the tuple, you ask?  Well:
    1. A Floor object, detailing the contents of the current floor.
          The Floor object contains, of course, many dudes, including a player.
    """
    
    retFloor = getSaveFloor(getFile(filename), 0, None, monster_factory)
    if delete_save:
        os.remove(filename)
    
    return (retFloor,)

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

def getDungeon(linelist, initline = 0, lastline = None):
    """
    An internal function that takes a map of terrain and returns a Dungeon.
    """
    if linelist[initline] != "[MAP]":
        raise ValueError("Dungeon data begins with %s, not [MAP]." % linelist[initline])
    
    endline = findTag(linelist, "[END]", initline, lastline)
    dimensions = (len(linelist[initline + 1]), endline - initline - 1)
    
    retDungeon = level.Dungeon(dimensions)
    
    for y in range(0, dimensions[1]):
        if len(linelist[y + initline + 1]) != dimensions[0]:
            raise ValueError(
                  "Line %d should be length %d, but is actually length %d." % 
                  (y + initline + 1, dimensions[0],
                   len(linelist[y + initline + 1])))
        retDungeon.panel[y] = linelist[y + initline + 1]
    
    return retDungeon

def setDudeLayer(linelist, initline, floor, lastline, monsterFactory):
    """
    Add the monsters in linelist to the floor provided.
    
    If lastline = None, it is not used.
    """
    
    if linelist[initline] != "[MONSTERS]":
        raise ValueError("Monster data begins with %s, not [MONSTERS]." % linelist[initline])
    
    endline = findTag(linelist, "[END]", initline, lastline)
    
    for i in range(initline + 1, endline):
        splitLine = linelist[i].split('=')
        name = splitLine[1]
        coords = coordinates.stringToCoords(splitLine[0])
        floor.addDude(monsterFactory.create(name, coords, floor))
    
def setSaveDudeLayer(linelist, initline, floor, lastline, monsterFactory):
    """
    Add the dudes in linelist, including a player, to the floor provided.
    
    If lastline = None, it is not used.
    """
    
    if linelist[initline] != "[DUDES]":
        raise ValueError("Monster data begins with %s, not [DUDES]." % linelist[initline])
    
    endline = findTag(linelist, "[END]", initline, lastline)
    
    for lineid in range(initline + 1, endline): #linelist[(initline + 1) : endline]:
        if linelist[lineid] == "(DUDE)":
            mon = getSaveDude(linelist, lineid, lastline, monsterFactory)
            if mon.isPlayer():
                floor.addPlayer(mon)
            else:
                floor.addDude(mon)

def getSaveDude(linelist, initline, lastline, monsterFactory):
    """
    Get a dude in save format (which contains more state info than in a floor.)
    """
    
    if linelist[initline] != "(DUDE)":
        raise ValueError("Monster data begins with %s, not (DUDE)." % linelist[initline])
    
    endline = findTag(linelist, "(ENDDUDE)", initline, lastline)
    attr_dict = labelDict(linelist, initline, endline)
    
    if attr_dict["type"] == "player":
        ret_dude = dude.Player(attr_dict["name"],
                               coordinates.stringToCoords(attr_dict["location"]),
                              )
    else:
        ret_dude = monsterFactory.create(attr_dict["type"],
                                         coordinates.stringToCoords(attr_dict["location"])
                                        )
    
    #log an error if current HP is greater than maximum HP
    log.pasAss(int(attr_dict["curhp"]) > ret_dude.max_HP,
               "curhp > maxhp (%s > %d) of %s at %s, id %s" %
               (attr_dict["curhp"], ret_dude.max_HP, ret_dude.name,
                str(ret_dude.coords), str(ret_dude.ID)))
    
    ret_dude.setHP(int(attr_dict["curhp"]))
    
    return ret_dude

def getElements(linelist, initline, lastline, dimensions):
    """
    Return a dungeon with the elements specified.
    """
    
    if linelist[initline] != "[ELEMENTS]":
        raise ValueError("Element data begins with %s, not [ELEMENTS]." % linelist[initline])
    
    retElements = level.Dungeon(dimensions)
    
    endline = findTag(linelist, "[END]", initline, lastline)
    for i in range(initline + 1, endline):
        splitLine = linelist[i].split('=')
        retElements[coordinates.stringToCoords(splitLine[0])] = splitLine[1]
    
    return retElements

def getFloor(linelist, initline, monsterFactory):
    """
    An internal function that returns a floor from a floor data file.
    
    Not to be used with saves, as saves require more detailed information on
    dudes.
    """
    
    if linelist[initline] != "<FLOOR>":
        raise ValueError("Floor data begins with %s, not <FLOOR>." % linelist[initline])
    lastline = findTag(linelist, "[ENDSEC]", initline)
    mapline = findTag(linelist, "[MAP]", initline, lastline)
    dudeline = findTag(linelist, "[MONSTERS]", initline, lastline)
    elemline = findTag(linelist, "[ELEMENTS]", initline, lastline)
    
    dungeon = getDungeon(linelist, mapline, lastline)
    elements = getElements(linelist, elemline, lastline, dungeon.dimensions)
    retFloor = level.Level(dungeon.dimensions, None, elements, dungeon)
    setDudeLayer(linelist, dudeline, retFloor, lastline, monsterFactory)
    
    return retFloor

def getSaveFloor(linelist, initline, lastline, monsterFactory):
    """
    An internal function that, given a line list, returns a playable floor.
    
    Used for saves only; as saves require more detailed dude information, they
    have a slightly different format.
    
    If "None" is given for lastline, no ending line is used.
    """
    
    if linelist[initline] != "<SFLOOR>":
        raise ValueError("Floor save data begins with %s, not <SFLOOR>." % linelist[initline])
    lastline = findTag(linelist, "[ENDSEC]", initline)
    mapline = findTag(linelist, "[MAP]", initline, lastline)
    dudeline = findTag(linelist, "[DUDES]", initline, lastline)
    elemline = findTag(linelist, "[ELEMENTS]", initline, lastline)
    
    dungeon = getDungeon(linelist, mapline, lastline)
    elements = getElements(linelist, elemline, lastline, dungeon.dimensions)
    retFloor = level.Level(dungeon.dimensions, None, elements, dungeon)
    setSaveDudeLayer(linelist, dudeline, retFloor, lastline, monsterFactory)
    
    return retFloor

def getMonsterFactory(linelist, initline = 0):
    """
    Returns a monster factory with the monsters detailed in the lines given.
    """
    
    curline = initline
    retFactory = dude.MonsterFactory()
    
    while 1: #continue loop until out of tags
        try:
            curline = findTag(linelist, "<MONSTER>", curline)
        except ValueError:
            break
        else:
            retFactory.append(getMonster(linelist, curline))
            curline += 1
    
    return retFactory

def getMonster(linelist, initline = 0):
    """
    Given the starting line, translate a text-file description into a Monster.
    """
    
    if linelist[0] != "<MONSTER>":
        raise ValueError("Monster data begins with %s, not <MONSTER>." % linelist[initline])
    
    lastline = findTag(linelist, "[ENDSEC]", initline)
    try: #get tags - findTag throws ValueError if there's no tag section
        tagline = findTag(linelist, "[TAG]", initline, lastline)
    except ValueError:
        tags = []
    else:
        endline = findTag(linelist, "[END]", tagline, lastline)
        tags = linelist[tagline + 1:endline]
    
    attrDict = labelDict(linelist, initline + 1, lastline)
    
    return dude.Monster(attrDict["name"],
                        None, 
                        symbol.Glyph(attrDict["glyph"], (255, 0, 0,)),
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
    dontGoPast.  findTag raises a ValueError exception if the tag isn't there.
    """
    
    for i in range(startLine, dontGoPast if dontGoPast is not None else len(linelist)):
        if tag == linelist[i]:
            return i
    
    raise ValueError("%s not found in list provided; try loosening range." % tag)

def outputSave(cur_level, save_name = None):
    """
    Output a save file, given state info.
    """
    
    if save_name is None:
        filename = cur_level.player.name + ".sav"
    else:
        filename = save_name
    
    with open(filename, "w") as save:
        
        save.write("<SFLOOR>\n")
        saveMap(save, cur_level.dungeon)
        saveDudes(save, cur_level)
        saveElements(save, cur_level.elements)
        save.write("[ENDSEC]")

def saveMap(save, dungeon_map):
    """
    Outputs a given map (a Dungeon) to a given file.
    """
    
    save.write("[MAP]\n")
    
    for line in dungeon_map.panel:
        save.write(line + "\n")
    
    save.write("[END]\n")


def saveDudes(save, cur_level):
    """
    Outputs a bunch of dudes, including the player, to a given file.
    """
    
    save.write("[DUDES]\n")
    
    for cur_dude in cur_level.dudeLayer:
        save.write("(DUDE)\n")
        if cur_dude.isPlayer():
            save.write("type=player\n")
            save.write("curhp=%d\n" % cur_dude.cur_HP)
            save.write("location=(%d,%d)\n" % (cur_dude.coords[0], cur_dude.coords[1]))
            save.write("name=%s\n" % cur_dude.name)
        else:
            save.write("type=%s\n" % cur_dude.name)
            save.write("curhp=%d\n" % cur_dude.cur_HP)
            save.write("location=(%d,%d)\n" % (cur_dude.coords[0], cur_dude.coords[1]))
        save.write("(ENDDUDE)\n")
    
    save.write("[END]\n")

def saveElements(save, elements):
    """
    Outputs a Dungeon of elements to a given file.
    """
    
    save.write("[ELEMENTS]\n")
    
    for y in range(elements.dimensions[1]):
        for x in range(elements.dimensions[0]):
            if elements[(x, y)] != ' ':
                save.write("(%d,%d)=%s\n" % (x, y, elements[(x, y)]))
    
    save.write("[END]\n")

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

if __name__ == "__main__":
    pass
#    ll = getFile("dungeon.txt")
#    dg = getDungeon(ll)
#    print dg
