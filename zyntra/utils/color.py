from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import requests
import random

@dataclass
class ColorData:
    name: str
    hex: str

class Color(Enum):
    red = "#FF0000"
    green = "#00FF00"
    blue = "#0000FF"
    yellow = "#FFFF00"
    black = "#000000"
    white = "#FFFFFF"
    orange = "#FFA500"
    purple = "#800080"
    pink = "#FFC0CB"
    cyan = "#00FFFF"
    magenta = "#FF00FF"
    brown = "#A52A2A"
    gray = "#808080"

    @staticmethod
    def rgb_to_hex(r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def get_color(name: str, fallback: Color = None):
        if fallback == None:
            fallback = Color.black

        for color in Color:
            if color.name == name.lower():
                return color.value
            
        return fallback.value
    
    @classmethod
    def random(cls):
        hx = cls.rgb_to_hex(random.randrange(0, 255, 1), random.randrange(0, 255, 1), random.randrange(0, 255, 1))
        resp = requests.get(f"https://api.color.pizza/v1/?values={hx.removeprefix("#")}")
        if (resp.status_code == 200):
            return ColorData(resp.json().get("paletteTitle", "Unknown"), hx)
        else:
            return None