import libtcodpy as libtcod


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

    # Holding keyboard and mouse input
    key = libtcod.Key()
    mouse = libtcod.Mouse()

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
