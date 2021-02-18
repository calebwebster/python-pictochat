LARGE_FONT = ("Maiandra GD", 22)
MEDIUM_FONT = ("Consolas Bold Italic", 12)
SMALL_FONT = ('Consolas Italic', 12)
TINY_FONT = ("Maiandra GD", 10)

try:
    from utils.dialogs import get_password, get_colour, get_drawing
except ModuleNotFoundError:
    print("[IMPORT FAILURE] Install additional modules to run Client.")
    
from utils.find_nth import find_nth
from utils.find_num_lines import find_num_lines
# from utils.install_font import install_font
import json

with open("utils/codes.json", "r") as codes_file:
    CODES = json.load(codes_file)

with open("utils/colours.json", "r") as colours_file:
    COLOURS = json.load(colours_file)

HEADER_LENGTH = 8
PORT = 5000
IMG_CHUNK_SIZE = 10000
FORMAT = "utf-8"
