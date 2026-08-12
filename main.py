from mmfparser.bytereader import ByteReader
from mmfparser.data.mfa import MFA
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

main()
