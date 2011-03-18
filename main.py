"""
The main loop; if you want to play, this is where you do it.
"""

USE_PROFILER = False

if USE_PROFILER:
    import cProfile

import cPickle

import tcod_display as display
import level
import dude
import pc
import config
import coordinates
import symbol
import fileio
import mapgen
import action
import exc
import kb

import log

def main(win = None):
    mainMonsterFactory = fileio.getMonsterFactory(
                         fileio.getFile("monsters.dat"))
    floor_defs = fileio.getFloorDefinitions(
                 mainMonsterFactory,
                 fileio.getFile("levels.dat"))

    try:
        save_data = fileio.restore_save("John Stenibeck.sav")
    except IOError:
# No save; load from a random dungeon instead.
        player = pc.Player("John Stenibeck", (40, 40))
        curlev = mapgen.nextLevel(floor_defs, 1, player)
    else:
        (player, floor) = save_data
        curlev = mapgen.nextLevel(floor_defs, floor, player)

    display.init()
    display.display_main_screen(curlev.getFOVArray(),
                                curlev.getPlayer().coords,
                                curlev.messages.getArray(),
                                curlev.getPlayer().getSidebar().getArray())

    while 1:
        try:
            curlev.next()
        except exc.LevelChange:
            new_floor = curlev.floor + 1
            curlev.player.clearMemory()
            fileio.save_game(curlev.player, new_floor)
            curlev = mapgen.nextLevel(floor_defs, new_floor, player)
            curlev.player.clearMemory()
            curlev.messages.append("Welcome to the next floor!")
            curlev.player.levelUp()
        except exc.SavingLevelChange:
            saved_player = curlev.player
            new_floor = curlev.floor + 1
            saved_player.levelUp()
            saved_player.clearMemory()
            saved_player.currentLevel = None
            fileio.save_game(saved_player, new_floor)
            return
        except exc.PlayerDeath:
            curlev.messages.say("You die.")
            kb.pause(curlev.messages)
            return

def entry():
    main()

def prof():
    cProfile.run('entry()', 'profile.pr')

if __name__ == "__main__":
    if USE_PROFILER:
        prof()
    else:
        entry()
