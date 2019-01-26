import libtcodpy as libtcod
from random import randint
from enum import Enum
import math


def handle_keys(key):
    """ Handle the keyboard inputs of the player """

    key_char = chr(key.c)

    # Movement keys
    if key.vk == libtcod.KEY_UP or key_char == "k":
        return {"move": (0, -1)}
    elif key.vk == libtcod.KEY_DOWN or key_char == "j":
        return {"move": (0, 1)}
    elif key.vk == libtcod.KEY_LEFT or key_char == "h":
        return {"move": (-1, 0)}
    elif key.vk == libtcod.KEY_RIGHT or key_char == "l":
        return {"move": (1, 0)}
    elif key_char == "y":
        return {"move": (-1, -1)}
    elif key_char == "u":
        return {"move": (1, -1)}
    elif key_char == "b":
        return {"move": (-1, 1)}
    elif key_char == "n":
        return {"move": (1, 1)}

    # Non-movement keys
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # left Alt + Enter: toggle fullscreen mode
        return {"fullscreen": True}

    if key.vk == libtcod.KEY_ESCAPE:
        # Exit the game
        return {"exit": True}

    # If no key pressed...
    return {}


def initialize_fov(game_map):
    """ Fiel of view initialization """

    fov_map = libtcod.map_new(game_map.width, game_map.height)

    for y in range(game_map.height):
        for x in range(game_map.width):
            libtcod.map_set_properties(fov_map,
                                       x,
                                       y,
                                       not game_map.tiles[x][y].block_sight,
                                       not game_map.tiles[x][y].blocked)

    return fov_map


def recompute_fov(fov_map, x, y, radius, light_walls=True, algorithm=0):
    libtcod.map_compute_fov(fov_map, x, y, radius, light_walls, algorithm)


class Fighter:
    """ Fighter component """

    def __init__(self, hp, defense, power):
        self.hp = hp
        self.defense = defense
        self.power = power

    def take_damage(self, amount):
        self.hp -= amount


class GameStates(Enum):
    PLAYER_TURN = 1
    ENEMY_TURN = 2


class BasicMonster:
    """ Basic ai for monsters """

    def take_turn(self, target, fov_map, game_map, entities):
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(target) >= 2:
                monster.move_astar(target, entities, game_map)
            elif target.fighter.hp > 0:
                print("the {0} insults you! Your ego is damaged!".format(monster.name))


class Entity:
    """ A generic object to represent players, enemies, items, etc. """

    def __init__(self, x, y, char, color, name, blocks=False, fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter
        self.ai = ai

        if self.fighter:
            self.fighter.owner = self

        if self.ai:
            self.ai.owner = self

    def move(self, dx, dy):
        """ Move the entity by a given amount """
        self.x += dx
        self.y += dy

    def move_towards(self, target_x, target_y, game_map, entities):
        """ Move the entity by a given amount toward a target """
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        if not (game_map.is_blocked(self.x + dx, self.y + dy) or get_blocking_entities_at_location(entities, self.x + dx, self.y + dy)):
            self.move(dx, dy)

    def move_astar(self, target, entities, game_map):
        """ Pathfinding algo to chase the player """
        # Create a FOV map that has the dimensions of the map
        fov = libtcod.map_new(game_map.width, game_map.height)

        # Scan the current map each turn and set all the walls as unwalkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                libtcod.map_set_properties(fov,
                                           x1,
                                           y1,
                                           not game_map.tiles[x1][y1].block_sight,
                                           not game_map.tiles[x1][y1].blocked)

        # Scan all the objects to see if there are objects
        # that must be navigated around
        # Check also that the object isn't self or the target
        # (so that the start and the end points are free)
        # The AI class handles the situation if self is next to the target
        # so it will not use this A* function anyway
        for entity in entities:
            if entity.blocks and entity != self and entity != target:
                # Set the tile as a wall so it must be navigated around
                libtcod.map_set_properties(fov, entity.x, entity.y, True, False)

        # Allocate a A* path
        # The 1.41 is the normal diagonal cost of moving,
        # it can be set as 0.0 if diagonal moves are prohibited
        my_path = libtcod.path_new_using_map(fov, 1.41)

        # Compute the path between self's coordinates
        # and the target's coordinates
        libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)

        # Check if the path exists, and in this case,
        # also the path is shorter than 25 tiles
        # The path size matters if you want the monster to use
        # alternative longer paths (for example through other rooms)
        # if for example the player is in a corridor
        # It makes sense to keep path size relatively low to keep the monsters
        # from running around the map if there's an alternative path
        # really far away
        if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
            # Find the next coordinates in the computed full path
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                # Set self's coordinates to the next path tile
                self.x = x
                self.y = y
        else:
            # Keep the old move fct as a backup so that if there are no paths
            # (for example another monster blocks a corridor)
            # it will still try to move towards the player
            # (closer to the corridor opening)
            self.move_towards(target.x, target.y, game_map, entities)

            # Delete the path to free memory
        libtcod.path_delete(my_path)

    def distance_to(self, other):
        """ Give the distance between the current entity and another one """

        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)


def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None


class Rect:
    """ Base shape for room creation """

    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        """ Returns the rectangle's center coordinates """
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return (center_x, center_y)

    def intersect(self, other):
        """ Returns true if this rectangle intersects with another one """
        return (self.x1 <= other.x2 and self.x2 >= other.x1
                and self.y1 <= other.y2 and self.y2 >= other.y1)


class Tile:
    """ A tile on the map.
        It may or may not be blocked,
        and may or may not block sight."""

    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
        # By default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight
        # Specify if the tile has been explored by the player or not
        self.explored = False


class GameMap:
    """ Game map creation """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = self._initialize_tiles()

    def _initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)]
                 for x in range(self.width)]
        return tiles

    def make_map(self, max_rooms, room_min_size, room_max_size,
                 map_width, map_height, player, entities,
                 max_monsters_per_room):
        """ Procedural generation of the rooms """

        rooms = []
        num_rooms = 0

        for r in range(max_rooms):
            # Random width and height
            w = randint(room_min_size, room_max_size)
            h = randint(room_min_size, room_max_size)
            # Random position without going out of the boundaries of the map
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)
            # Creation of the room
            new_room = Rect(x, y, w, h)
            # Run through the other rooms and see if they
            # intersect with this one
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break
            else:
                # The new room doesn't interect with any of the previous ones
                self.create_room(new_room)
                # Center coordinates of the new room
                (new_x, new_y) = new_room.center()

                if num_rooms == 0:
                    # This is the first room, where the player starts at
                    player.x = new_x
                    player.y = new_y
                else:
                    # For all rooms after the first: connect it to the previous
                    # room with a tunnel

                    # Center coordinates of the previous room
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()
                    # Flip a coin
                    if randint(0, 1) == 1:
                        # First move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # First move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                self.place_entities(new_room, entities, max_monsters_per_room)

                # Finally, append the new room to the list
                rooms.append(new_room)
                num_rooms += 1

    def create_room(self, room):
        """ Go through the tiles in the rectangle and make them passable """

        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        """ horizontal tunnel creation"""

        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        """ vertical tunnel creation"""

        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def place_entities(self, room, entities, max_monsters_per_room):
        """ Place entities in the rooms """

        # Get a random number of monsters
        number_of_monster = randint(0, max_monsters_per_room)

        for i in range(number_of_monster):
            # Choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities
                        if entity.x == x and entity.y == y]):
                if randint(0, 100) < 80:
                    fighter_component = Fighter(hp=10, defense=0, power=3)
                    ai_component = BasicMonster()
                    monster = Entity(x,
                                     y,
                                     "#",
                                     libtcod.desaturated_green,
                                     "Small nightmare",
                                     blocks=True,
                                     fighter=fighter_component,
                                     ai=ai_component)
                else:
                    fighter_component = Fighter(hp=16, defense=1, power=4)
                    ai_component = BasicMonster()
                    monster = Entity(x,
                                     y,
                                     "%",
                                     libtcod.darker_green,
                                     "Big nightmare",
                                     blocks=True,
                                     fighter=fighter_component,
                                     ai=ai_component)

                entities.append(monster)

    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True
        return False


def main():
    # Constants definition
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 80
    MAP_HEIGHT = 45
    ROOM_MAX_SIZE = 10
    ROOM_MIN_SIZE = 6
    MAX_ROOMS = 30
    FOV_ALGORITHM = 1
    FOV_LIGHT_WALLS = True
    FOV_RADIUS = 6
    MAX_MONSTERS_PER_ROOM = 3

    # Colors dict
    colors = {
        "dark_wall": libtcod.Color(0, 0, 100),
        "dark_ground": libtcod.Color(50, 50, 150),
        "light_wall": libtcod.Color(130, 110, 50),
        "light_ground": libtcod.Color(200, 180, 50),
    }

    # Entities init
    fighter_component = Fighter(hp=30, defense=2, power=5)
    player = Entity(0,
                    0,
                    "@",
                    libtcod.white,
                    "Player",
                    blocks=True,
                    fighter=fighter_component)
    entities = [player]

    # Font setting
    libtcod.console_set_custom_font("arial10x10.png",
                                    libtcod.FONT_TYPE_GRAYSCALE
                                    | libtcod.FONT_LAYOUT_TCOD)

    # Creation of the screen
    libtcod.console_init_root(SCREEN_WIDTH,
                              SCREEN_HEIGHT,
                              "Selen's dream",
                              False)

    # Creation of the main console
    con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Game's map init
    game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
    game_map.make_map(MAX_ROOMS,
                      ROOM_MIN_SIZE,
                      ROOM_MAX_SIZE,
                      MAP_WIDTH,
                      MAP_HEIGHT,
                      player,
                      entities,
                      MAX_MONSTERS_PER_ROOM)

    # field of view init
    fov_recompute = True
    fov_map = initialize_fov(game_map)

    # Holding keyboard and mouse input
    key = libtcod.Key()
    mouse = libtcod.Mouse()

    # Game state init
    game_state = GameStates.PLAYER_TURN

    # Main game Loop
    while not libtcod.console_is_window_closed():
        # Capture new events
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS,
                                    key,
                                    mouse)

        # Recompute fov if needed

        # Render all

        libtcod.console_flush()

        # Clear entities

        # Manage events
        action = handle_keys(key)

        move = action.get("move")
        exit = action.get("exit")
        fullscreen = action.get("fullscreen")

        if move:
            pass

        if exit:
            return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)


if __name__ == '__main__':
    main()
