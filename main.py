from mmfparser.bytereader import ByteReader
from mmfparser.data.mfa import MFA, ObjectLoader
from mmfparser.data.chunkloaders.movement import Path as PathLoader
import json

class Screen:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.layers = {}

    def to_dict(self):
        # Recursively convert tiles to dictionaries
        layers = { index: [tile.to_dict() for tile in layer] for (index, layer) in self.layers.items() }
        return { 'x': self.x, 'y': self.y, 'layers': layers }

class TileOrObject:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name

    def to_dict(self):
        return { 'x': self.x, 'y': self.y, 'name': self.name }

def print_recursive(x, indent=''):
    if isinstance(x, list) or isinstance(x, tuple):
        print('{0}['.format(indent))
        for (i, item) in enumerate(x):
            print('{0}  {1}:'.format(indent, i))
            print_recursive(item, indent + '    ')
        print('{0}]'.format(indent))
    elif type(x) in [int, long, float, str, bool, type(None)]:
        print('{0}{1}'.format(indent, x))
    else:
        props = x if isinstance(x, dict) else x.__dict__
        print('{0}{{'.format(indent))
        for (key, value) in props.items():
            print('{0}  {1}:'.format(indent, key))
            print_recursive(value, indent + '    ')
        print('{0}}}'.format(indent))        

def main():
    reader = ByteReader(open('Knytt27.mfa', 'rb'))
    mfa = MFA()
    mfa.initialize()
    mfa.read(reader)

    main_level = next(x for x in mfa.frames if x.name == "The Level")
    screens_dict = parse_screens(main_level)

    # Sort screens by position
    screens_sorted = []
    for key in sorted(screens_dict.keys()):
        screen = screens_dict[key]
        # Sort tiles by position
        for (index, layer) in screen.layers.items():
            layer.sort(key=lambda tile: (tile.x, tile.y))
        screens_sorted.append(screen)

    with open("map.json", "w") as file:
        screens_serializable = [screen.to_dict() for screen in screens_sorted]
        json.dump(screens_serializable, file)

    all_path_movements = {}
    for item in main_level.items:
        path_movements = get_path_movements(item)
        if len(path_movements) > 0:
            all_path_movements[item.name] = [path_movement_to_dict(x) for x in path_movements]

    with open("paths.json", "w") as file:
        json.dump(all_path_movements, file)

def parse_screens(frame):
    item_dict = {}
    for item in frame.items:
        item_dict[item.handle] = item

    screens = {}

    for instance in frame.instances:
        global_x = instance.x
        global_y = instance.y
        
        map_x = instance.x // 600
        map_y = instance.y // 240
        map_pos = (map_x, map_y)
        if map_x < 0 or map_y < 0:
            continue
        
        screen_x = global_x - map_x * 600
        screen_y = global_y - map_y * 240

        item_name = item_dict[instance.itemHandle].name
        tile = TileOrObject(screen_x, screen_y, item_name)

        if map_pos not in screens:
            screens[map_pos] = Screen(map_x, map_y)
        screen = screens[map_pos]
        
        layer_index = instance.layer
        if layer_index not in screen.layers:
            screen.layers[layer_index] = []
        layer = screen.layers[layer_index]
        layer.append(tile)

    return screens

def get_path_movements(item):
    # `loader` has the specialized data for the specific item type
    # For objects that move, it will be an instance of Active (mmfparser/data/mfa.py:558)
    # Active inherits from AnimationObject, which inherits from ObjectLoader, which populates `movements` (mmfparser/data/mfa.py:431)
    if not isinstance(item.loader, ObjectLoader): return []
    movements = item.loader.movements.items
    
    # Filter to just path movements
    return [x for x in movements if isinstance(x.loader, PathLoader)]

def path_movement_to_dict(movement):
    # Again, the specialized data for the specific movement type is stored in `loader`
    # For paths, this will be an instance of Path (mmfparser/data/chunkloaders/movement.py:133)
    return {
        "movingAtStart": movement.movingAtStart,
        "directionAtStart": movement.directionAtStart,
        "minimumSpeed": movement.loader.minimumSpeed,
        "maximumSpeed": movement.loader.maximumSpeed,
        "loop": movement.loader.loop,
        "repositionAtEnd": movement.loader.repositionAtEnd,
        "reverseAtEnd": movement.loader.reverseAtEnd,
        "steps": [path_step_to_dict(x) for x in movement.loader.steps]
    }

def path_step_to_dict(step):
    # Each point in the path is an instance of Step (mmfparser/data/chunkoaders/movement.py:174)
    # The destination will be in world coordinates, of course
    vals = {
        "speed": step.speed,
        "direction": step.direction,
        "destinationX": step.destinationX,
        "destinationY": step.destinationY,
        "cosinus": step.cosinus,
        "sinus": step.sinus,
        "length": step.length,
        "pause": step.pause
    }
    if step.name:
        vals['name'] = step.name
    return vals

main()
