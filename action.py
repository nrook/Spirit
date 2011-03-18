"""
Defines a central Action class, which includes any in-game actions dudes take.

Also included are sub-classes for specific Actions.  Note that no Actions
include code to actually perform themselves; they are strictly data.  The
Action module also includes various formulas, such as the damage dealt by an
attack or the HP gained on gaining a level.
"""

"""
Codes:

Quit (unused): QUIT
Move: MOVE
Stand still: WAIT
Standard attack: STDATK
Special melee attack: SPMELEE
Explode: EXPLODE
Fire an arrow: ARROW
Go upstairs: UP
Heal: HEAL
"""

"""
Spec codes are codes for special attacks or actions used by the player or a
monster.  Most monsters have a spec code representing the single type of
special attack they can use.

Spec codes:
Melee attacks:
CRITICAL: Perform a critical hit, with a CRIT_MULTIPLIER damage multiplier.
"""

import coordinates
import rng
import events
import tcod_display as display
import exc
import symbol
import cond
import config
import kb

CRIT_MULTIPLIER = 2
KNOCK_DAMAGE = 5
KNOCK_DISTANCE = 10

HEAL_HP_FOR_BONUS = 4

ARROW_GLYPH = symbol.Glyph('`', (255, 255, 255))

class Action(object):
    """
    An object representing an action a dude could take.
    Also includes a do() method, which actually does said action.

    Fields:
    strcode - a code representing the Action's type.  Use getCode() instead.
    message - a string representing a message to be displayed when the Action
        is taken.
    """
    
    def __init__(self, strcode, message = ""):
        """
        strcode is a code representing the type of action.
        
        As no generic Actions should exist, it should only be called by
        subclasses of Action.
        """
        
        self.strcode = strcode
        self.message = message
    
    def getCode(self):
        return self.strcode

    def do(self):
# The "do" method must return the number of ticks the action took.
        assert False
        return 0

class DoNothing(Action):
    """
    An object representing a dude not taking an action, not even using a turn.

    Fields:
    strcode - "DO NOTHING".
    """

    def __init__(self):
        Action.__init__(self, "DO NOTHING")

class Move(Action):
    """
    Fields:
    source - the Dude moving.
    coords - the relative coordinates to which the Dude is moving.  For
        instance, if coords = (1, 0) and source is at (2, 2), it will move
        to (3, 2).
    """
    
    def __init__(self, source, coords):
        """
        Coords should be the relative coords of the destination to the source.
        """
        
        Action.__init__(self, "MOVE")
        self.source = source
        self.coords = coords
    
    def getCoords(self):
        return self.coords

    def do(self):
        """
        Move the source of the action in the direction specified.
        Raise a ValueError if such a move is illegal.
        
        act - the action to be performed.

        Returns True if the move can be performed, and returns False if it
        cannot.
        """
        destination_coords = coordinates.add(self.source.coords, self.coords)

        if self.source.canMove(destination_coords):
            self.source.currentLevel.moveDude(self.source, destination_coords)
            return self.source.speed
        else:
            assert False
            return 0

class Heal(Action):
    """
    An action representing a dude being healed.
    """

    def __init__(self, source, destination, magnitude, hp_bonus):
        """
        destination - the dude being healed.
        magnitude - the amount of HP the dude should be healed.
        hp_bonus - true if the dude being healed should get a max HP bonus
                   for overhealing, false otherwise.
        """

        Action.__init__(self, "HEAL")
        self.source = source
        self.destination = destination
        self.magnitude = magnitude
        self.hp_bonus = hp_bonus

    def do(self):
        if self.destination.isPlayer():
            self.source.currentLevel.messages.say("You feel better.")
            extra_HP = (self.destination.cur_HP + self.magnitude 
                - self.destination.max_HP)

            if self.hp_bonus:
                if extra_HP <= 0:
                    self.destination.setHP(self.destination.cur_HP 
                        + self.magnitude)
                else:
                    if extra_HP <= 4:
                        HP_bonus = 1
                    else:
                        HP_bonus = extra_HP // 4
                        HP_overflow = extra_HP - (HP_bonus * 4)
                        HP_bonus += rng.percentChance(HP_overflow * 25)
                    self.destination.max_HP += HP_bonus
                    self.destination.setHP(self.destination.max_HP)
            else:
                if extra_HP <= 0:
                    self.destination.setHP(self.destination.cur_HP 
                        + self.magnitude)
                else:
                    self.destination.setHP(self.destination.max_HP)
        else:
            self.source.currentLevel.messages.say(
                "%(DESTINATION_NAME)s looks healthier."
                % {"DESTINATION_NAME":self.destination.getName()})
            self.destination.setHP(self.destination.cur_HP + magnitude)
        
        return self.source.speed

class Teleport(Action):
    """
    An action representing a move by a dude to any square.
    """

    def __init__(self, source, destination):
        """
        source - the dude teleporting.
        destination - the dude's destination.
        """
        
        Action.__init__(self, "TELEPORT")
        self.source = source
        self.destination = destination

    def do(self):
        if self.source.currentLevel.isEmpty(self.destination) \
            and self.destination not in self.source.currentLevel.dudeLayer:

            self.source.currentLevel.makeNoise("%(SOURCE_NAME)s suddenly disappears!"
                % {"SOURCE_NAME":self.source.getName()}, self.source.coords)
            self.source.currentLevel.moveDude(self.source, self.destination)
            self.source.currentLevel.makeNoise(
                "%(SOURCE_NAME)s appears out of thin air!"
                % {"SOURCE_NAME":self.source.getName()}, self.source.coords)
            return self.source.speed
        else:
            assert False
            return 0

class Up(Action):
    """
    An action representing an attempt to move up a level.
    """
    def __init__(self):
        Action.__init__(self, "UP")
    
class Quit(Action):
    """
    An action that represents the player's desire to quit the game.
    """
    
    def __init__(self):
        Action.__init__(self, "QUIT")

class Wait(Action):
    """
    An action that represents staying in place.

    Fields:
    source - the Dude waiting.
    """
    
    def __init__(self, source):
        Action.__init__(self, "WAIT")

        self.source = source

    def do(self):
        """
        Have the dude stand in place.
        """

        return self.source.speed

class Attack(Action):
    """
    An action that represents attacking another dude.

    Instance fields:
    source - the dude attacking.
    target - the dude getting attacked.
    """
    
    def __init__(self, source, target, message = "%(SOURCE_NAME)s attacks %(TARGET_NAME)s! (%(DAMAGE)d)"):
        Action.__init__(self, "STDATK", message)
        self.source = source
        self.target = target

    def do(self):
        """
        Have the source of the action attack its target.

        act - the action to be performed.

        Returns True.
        """
        damage_dealt = damage(self.source.attack, self.target.defense,
                       self.source.char_level, self.target.char_level)

        self.source.currentLevel.makeNoise(self.message % {
            "SOURCE_NAME": self.source.getName(),
            "DAMAGE": damage_dealt,
            "TARGET_NAME": self.target.getName()},
            self.source.coords)
        self.target.cur_HP -= damage_dealt
        self.target.checkDeath()

        return self.source.speed

class SpecialMelee(Action):
    """
    An action that represents attacking an adjacent dude with a special
    ability.
    
    Instance fields:
    source - the dude attacking.
    target - the dude being attacked.
    code - a special code representing the type of special attack.
    """

    def __init__(self, source, target, code, message = 
        "%(SOURCE_NAME)s uses a special attack on %(TARGET_NAME)s! (%(DAMAGE)d)"):

        Action.__init__(self, "SPMELEE", message)
        self.source = source
        self.target = target
        self.code = code

    def do(self):
        do_special_melee(self.code, self.source, self.target)
        return self.source.speed

class BombTick(Action):
    """
    An action representing a dude's TimeBomb condition ticking down.
    """

    def __init__(self, source):
        Action.__init__(self, "BOMBTICK", None)
        self.source = source

    def do(self):
        bomb_condition = self.source.conditions["timebomb"]
        bomb_condition.timer -= 1
        self.source.currentLevel.refreshDudeGlyph(self.source)
        return self.source.speed

class Detonate(Action):
    """
    An action representing a dude exploding, causing damage all around.
    """

    EXPLOSION_GLYPH = symbol.Glyph('#', (255, 0, 0))

    def __init__(self, source):
        Action.__init__(self, "DETONATE", None)
        self.source = source
        self.damage = self.source.max_HP / 2

    def do(self):
        level_ = self.source.currentLevel

        explosion_radius = coordinates.radius(1, self.source.coords, level_.dimensions)

        for coords in explosion_radius:
            level_.addSolidEffect(coords, self.EXPLOSION_GLYPH)

        kb.question(level_.messages, "%s explodes (%d)! --MORE--" % (self.source.getName(), self.damage))

        for explosion_coords in explosion_radius:
            if explosion_coords in level_.dudeLayer:
                target = level_.dudeLayer[explosion_coords]
                if target is not self.source:
                    target.cur_HP -= self.damage
                    target.currentLevel.removeSolidEffect(target.coords, self.EXPLOSION_GLYPH)
                    target.currentLevel.addSolidEffect(target.coords, self.EXPLOSION_GLYPH)
                    target.checkDeath()

        for coords in explosion_radius:
            level_.removeSolidEffect(coords, self.EXPLOSION_GLYPH)

        self.source.die()

        return self.source.speed

class Explode(Action):
    """
    An action representing an attack on a square and its adjacent squares.

    Explosions are fixed-damage.
    """

    def __init__(self, level_, coords, damage):
        Action.__init__(self, "EXPLODE", None)
        self.level_ = level_
        self.coords = coords
        self.damage = damage

    def do(self):
        for explosion_coords in coordinates.radius(1, self.coords, self.level_.dimensions):
            if explosion_coords in self.level_.dudeLayer:
                target = self.level_.dudeLayer[explosion_coords]
                target.cur_HP -= self.damage
                self.level_.messages.append("%s is hurt by the explosion! (%d)" %
                    (target.getName(), self.damage))
                target.checkDeath()

        return 0

class FireArrow(Action):
    """
    An action representing an arrow being fired in a direction, dealing damage
    equivalent to that of a physical attack.
    """

    def __init__(self, source, direction, distance):
        """
        Initialize an arrow-firing Action.
        
        source - the dude firing the arrow.
        direction - the direction in which the arrow is fired.
        distance - the maximum range the arrow can fly.
        """
        Action.__init__(self, "ARROW", "%s shot an arrow!" % source.getName())
        self.source = source
        self.direction = direction
        self.distance = distance

    def do(self):
        current_location = self.source.coords
        self.source.currentLevel.addSolidEffect(current_location, ARROW_GLYPH)
        self.source.currentLevel.makeNoise(
            self.message % {"SOURCE_NAME": self.source.getName()},
            self.source.coords)

        i = 0
        while True:
            i += 1
            display.refresh_screen()
            self.source.currentLevel.removeSolidEffect(current_location, ARROW_GLYPH)
            current_location = coordinates.add(current_location, self.direction)
            self.source.currentLevel.addSolidEffect(current_location, ARROW_GLYPH)

            if not self.source.currentLevel.isEmpty(current_location):
                break # If the arrow runs into a wall, just stop.
            elif current_location in self.source.currentLevel.dudeLayer:
                # The arrow hit a dude!
                target = self.source.currentLevel.dudeLayer[current_location]
                damage_dealt = damage(self.source.attack, target.defense,
                               self.source.char_level, target.char_level)
                self.source.currentLevel.makeNoise(
                    "The arrow hit %s. (%d)"
                    % (target.getName(), damage_dealt),
                    self.source.coords)
                display.refresh_screen()
                target.cur_HP -= damage_dealt
                target.checkDeath()
                self.source.currentLevel.removeSolidEffect(current_location, ARROW_GLYPH)
                break
            else:
                if i >= 12:
                    self.source.currentLevel.removeSolidEffect(current_location, ARROW_GLYPH)
                    display.refresh_screen()
                    break

        return self.source.speed

class Pounce(Action):
    """
    An action representing a distance-closing pounce attack.
    """

    def __init__(self, source, direction, distance):
        """
        Initialize a pounce Action.
        
        source - the dude pouncing.
        direction - the direction in which the pounce is made.
        distance - the maximum range of the pounce.
        """
        Action.__init__(self, "POUNCE", "")
        self.source = source
        self.direction = direction
        self.distance = distance

    def do(self):
        cur_lev = self.source.currentLevel
        next_loc = self.source.coords

# Essentially a for loop, for i in range(self.distance).
        i = 0
        while True:
            if i >= self.distance:
                cur_lev.messages.append("%s pounced, but caught only air."
                    % self.source.getName())
                break

            i += 1

            next_loc = coordinates.add(self.source.coords, self.direction)
            display.refresh_screen()
            
            if not cur_lev.isEmpty(next_loc):
                cur_lev.messages.append("%s pounced at the wall."
                    % self.source.getName())
                break
            elif next_loc in cur_lev.dudeLayer:
                # The pouncer hit a dude.
                target = cur_lev.dudeLayer[next_loc]
                # Bounce off: behind the dude if possible, in front otherwise.
                behind = coordinates.add(next_loc, self.direction)
                in_front = coordinates.subtract(next_loc, self.direction)

                if (cur_lev.isEmpty(behind) and behind not in cur_lev.dudeLayer):
                    cur_lev.moveDude(self.source, behind)
# The pouncer should already be in front of the target, so if it is not going
# through them, no motion is necessary.

                damage_dealt = damage(self.source.attack, target.defense,
                               self.source.char_level, target.char_level)
                cur_lev.messages.append("%s pounced on %s! (%d)"
                    % (self.source.getName(), target.getName(), damage_dealt))
                target.cur_HP -= damage_dealt
                target.checkDeath()
                break

            else:
                cur_lev.moveDude(self.source, next_loc)

        display.refresh_screen()
        return self.source.speed

class ThrowGrenade(Action):
    """
    An action representing a grenade hurled short-range to a specific square.
    """

    def __init__(self, source, target_coords):
        Action.__init__(self, "GRENTHROW", "%(SOURCE_NAME)s threw a grenade!")
        self.source = source
        self.target_coords = target_coords

    def do(self):
        self.source.currentLevel.makeNoise(self.message
            % {"SOURCE_NAME": self.source.getName()},
            self.source.coords)

        if self.target_coords in self.source.currentLevel.dudeLayer:
            target = self.source.currentLevel.dudeLayer[self.target_coords]
            self.source.currentLevel.makeNoise(
                "The grenade lands right on the %s!" % target.getName(),
                self.target_coords)
            return Detonate(target).do()

        grenade = self.source.currentLevel.definition.monster_factory.create("grenade")
        self.source.currentLevel.addDude(grenade, self.target_coords)
        grenade.giveCondition(cond.TimeBomb(3))
        return self.source.speed

class HasteMonster(Action):
    """
    An action representing applying the Haste status to a dude.
    """

    def __init__(self, source, target, duration):
        Action.__init__(self, "HASTEMON", "%(TARGET_NAME)s speeds up!")
        self.source = source
        self.target = target
        self.duration = duration

    def do(self):
        if not self.target.hasCondition("haste"):
            self.target.currentLevel.makeNoise(self.message
                % {"TARGET_NAME": self.target.getName()}, self.target.coords)
            self.target.giveCondition(cond.Haste(self.duration))
        return self.source.speed

class HasteAll(Action):
    """
    An action representing Hasting all of the dudes in view.
    """

    def __init__(self, source, duration, hit_user, hit_player):
        """
        source - the thing doing the hasting.
        duration - the number of turns the hasting should last.
        hit_user - whether the source should be hasted. If it should, it is
                   hasted for twice as long as the monsters.
        hit_player - whether the player should be hasted, if in range.
        """

        Action.__init__(self, "HASTEALL", "The air itself quickens around %(SOURCE_NAME)s!")
        self.source = source
        self.duration = duration
        self.hit_user = hit_user
        self.hit_player = hit_player

    def do(self):
        self.source.currentLevel.makeNoise(self.message 
            % {"SOURCE_NAME": self.source.getName()}, self.source.coords)
        if self.hit_user:
            HasteMonster(self.source, self.source, self.duration * 2).do()
        for d in self.source.fov.dudes:
            if (not d.isPlayer()) or self.hit_player:
                HasteMonster(self.source, d, self.duration).do()

        return self.source.speed

class Summon(Action):
    """
    An action representing the boss summoning foes.
    """

    CENTER = (24, 24)
    SUMMONS = ( (
        ("lancer", (-1, -1)),
        ("lancer", (-1, 1)),
        ("lancer", (1, -1)),
        ("lancer", (1, 1))
    ), (
        ("boxer", (2, 0)),
        ("boxer", (-2, 0))
    ), (
        ("Bertrand the Whisperer", (0, 0)),
    ) )

    def __init__(self, level_, prev_summons):
        Action.__init__(self, "SUMMON", "Enemies ahoy!")
        self.level_ = level_
        self.prev_summons = prev_summons
    
    def do(self):
        if self.prev_summons < len(self.SUMMONS):
            self.level_.messages.append(self.message)
            enemy_list = self.SUMMONS[self.prev_summons]
            for (name, coords) in enemy_list:
                real_coords = coordinates.add(coords, self.CENTER)
                mon = self.level_.createMonster(name, real_coords)

def is_generic_action(act):
    """
    Return True if the action passed is a generic action both lots of players
    and lots of monsters could be expected to do.

    Currently, the following actions are considered generic:
    - Attack
    - Move
    - Wait
    """

    code = act.getCode()
    if code in ("STDATK", "MOVE", "WAIT"):
        return True
    else:
        return False

def do_generic_action(act):
    """
    Perform the generic action passed.  Return True if this action takes up
    a turn.  (Currently, this will always be the case.)

    act - the action to be performed.

    Raises a ValueError if is_generic_action(act) is false.
    """

    if not is_generic_action(act):
        raise ValueError("The act, %s, is not a generic action." % str(act))

    return act.do()

def do_special_melee(attack_type, source, target):
    """
    Have a Dude perform a special melee attack.

    attack_type - a string representing the type of special attack.
    source - the Dude attacking.
    target - the Dude being attacked.
    """

    if attack_type == "CRITICAL":
        damage_dealt = CRIT_MULTIPLIER * \
                       damage(source.attack, target.defense,
                              source.char_level, target.char_level)
        source.currentLevel.makeNoise(
        "%(SOURCE_NAME)s runs %(TARGET_NAME)s all the way through! (%(DAMAGE)d)"
            % {"SOURCE_NAME": source.getName(),
               "DAMAGE": damage_dealt,
               "TARGET_NAME": target.getName()},
            source.coords)
        target.cur_HP -= damage_dealt
        target.checkDeath()
    elif attack_type == "KNOCK":
        damage_dealt = KNOCK_DAMAGE
        direction = coordinates.subtract(target.coords, source.coords)
        source.currentLevel.makeNoise(
        "%(SOURCE_NAME)s delivers a wicked punch to %(TARGET_NAME)s! (%(DAMAGE)d)"
            % {"SOURCE_NAME": source.getName(),
               "DAMAGE": damage_dealt,
               "TARGET_NAME": target.getName()},
            source.coords)
        for i in range(KNOCK_DISTANCE):
            display.refresh_screen()
            destination = coordinates.add(target.coords, direction)
            if target.canMove(destination):
                target.currentLevel.moveDude(target, destination)
            else:
                break
        display.refresh_screen()
        target.cur_HP -= damage_dealt
        target.checkDeath()
    elif attack_type == "EXPLODE":
        explode_action = Explode(source.currentLevel, source.coords, 10)
        source.currentLevel.makeNoise(
            "%(SOURCE_NAME)s explodes!" % {"SOURCE_NAME": source.getName()},
            source.coords)
        explode_action.do()
    elif attack_type == "STICK":
        damage_dealt = damage(source.attack, target.defense,
                       source.char_level, target.char_level) / 5
        source.currentLevel.makeNoise(
        "%(SOURCE_NAME)s spins a web around %(TARGET_NAME)s! (%(DAMAGE)d)"
            % {"SOURCE_NAME": source.getName(),
               "DAMAGE": damage_dealt,
               "TARGET_NAME": target.getName()},
            source.coords)
        target.giveCondition(cond.Stuck(8))
        target.cur_HP -= damage_dealt
        target.checkDeath()
    else:
        raise exc.InvalidDataWarning("%s special ability used by %s on %s."
                                     % (attack_type, str(source), str(target)))

def expected_HP(dude_level):
        return 6 * (dude_level + 2)

def HP_on_level_gain():
    """
    Determines what maximum HP increase the player gets on level gain.
    """
    
    return 4

def damage(attack_power, defense_modifier, attacker_level, defender_level):
        defense_modifier = float(defense_modifier) / 100
        return attack_power * defense_modifier
