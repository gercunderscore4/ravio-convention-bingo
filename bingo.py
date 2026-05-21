"""
Take a bingo SVG and replace its contents with randomized tiles.

Exaples of inkex use:
https://inkscape-extensions-guide.readthedocs.io/en/latest/02_hello-world.html

Need to ensure that inkscape is in PATH for the SVG to PDF commands.

https://github.com/duttad/mergepdfs
python -m pip install git+https://github.com/duttad/mergepdfs.git
"""

import random
import re
import subprocess
from enum import Enum
from pathlib import Path

from inkex.elements import TextElement
from pypdf import PdfWriter


SVG_PATH = "bingo_card.svg"
CARD_DIR = "cards"
MERGED_PATH = "merged_cards.pdf"


ANIME_ENTRIES = [
    "Attack on Titan",
    "Apothecary Diaries",
    "Bleach",
    "Cardcaptors",
    "Castlevania",
    "Chainsaw Man",
    "Cowboy Bebop",
    "Dandadan",
    "Death Note",
    "Delicious in Dungeon",
    "Demon Slayer",
    "Digimon",
    "Dragon Ball",
    "Evangelion",
    "Fate",
    "Fire Force",
    "Frieren",
    "Fullmetal Alchemist",
    "Ghibli",
    "Gundam",
    "Gurren Lagann",
    "Hatsune Miku",
    "Hazbin Hotel",
    "Hellsing",
    "Hunter x Hunter",
    "Inuyasha",
    "JJK",
    "Jo-Jo's",
    "Kill la Kill",
    "Konosuba",
    "Kpop Demon Hunters",
    "My Dress up Darling",
    "My Hero Academia",
    "Naruto",
    "One Piece",
    "One Punch Man",
    "Pokemon",
    "RWBY",
    "Sailor Moon",
    "Sword Art Online",
    "Spy X Family",
    "Trigun",
    "Yu-gi-oh",
]


GAME_ENTRIES = [
    "Deltarune",
    "Devil May Cry",
    "Dungeons and Dragons",
    "Expedition 33",
    "Fallout",
    "Final Fantasy",
    "Genshin Impact",
    "Halo",
    "Helldivers",
    "Hollow Knight",
    "Kingdom Hearts",
    "League of Legends",
    "Legend of Zelda",
    "Mario",
    "Mass Effect",
    "Metal Gear",
    "Metroid",
    "Monster Hunter",
    "Nier",
    "Overwatch",
    "Persona",
    "Resident Evil",
    "Smash Bros",
    "Sonic",
    "StarFox",
    "Street Fighter",
    "Umamusume",
    "Witcher",
    "Zenless Zone Zero",
]

GENERIC_ENTRIES = [
    "sword",
    "shield",
    "hammer",
    "archer",
    "mage",
    "gunslinger",
    "armour",
    "giant",
    "samurai",
    "ninja",
    "knight",
    "royalty",
    "furry",
    "photographer",
    "school uniform",
    "winged",
    "maid",
]

COLOUR_ENTRIES = [
    "black and white",
    "blue and black",
    "blue and green",
    "blue and white",
    "blue and yellow",
    "green and black",
    "green and white",
    "green and yellow",
    "red and black",
    "red and blue",
    "red and green",
    "red and white",
    "red and yellow",
    "yellow and black",
    "yellow and white",
]

MATERIAL_ENTRIES = [
    "EVA foam",
    "Worbla",
    "cardboard",
    "PVC pipe",
    "embroidery",
    "fabric",
    "3D print",
    "with lights",
]

LOCATION_ENTRIES = [
    "water tower",
    "TCC sign",
    "parking lot",
    "photoshoot",
    "food trucks",
    "Delta",
    "TCC front entrance",
    "North Building",
]

class Symbol(Enum):
    WORLD = 0
    OUTFIT = 1
    LOCATION = 2


LIST_OF_SYMBOL_ENTRY_LIST_PAIRS = [
    (Symbol.OUTFIT, GENERIC_ENTRIES),
    (Symbol.OUTFIT, COLOUR_ENTRIES),
    (Symbol.OUTFIT, MATERIAL_ENTRIES),
    (Symbol.WORLD, ANIME_ENTRIES),
    (Symbol.WORLD, GAME_ENTRIES),
    (Symbol.WORLD, ANIME_ENTRIES),  # double these up for odds
    (Symbol.WORLD, GAME_ENTRIES),
    (Symbol.LOCATION, LOCATION_ENTRIES),
]

# SVG strings for edits/traversal

SQUARE_STR = 'inkscape:label="square"'
FILL_STR = "fill-opacity:1"
BLANK_STR = "fill-opacity:0"
WORLD_STR = "#6a6a6a"  # gave these slightly different colours so I can regex them
OUTFIT_STR = "#6b6b6b"
LOCATION_STR = "#6c6c6c"
TEXT_TAG_STR = "<text"
LINE1_STR = "Textbox1"
LINE2_STR = "Textbox2"

MOVE_MM = 36.0

# Proper XML code

INKSCAPE_NS = {
   "inkscape": "http://www.inkscape.org/namespaces/inkscape",
   "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
   "": "http://www.w3.org/2000/svg",
   "svg": "http://www.w3.org/2000/svg",
}


def find_wo_ns(parent, name):
    """find while ignoring namespace"""
    for element in parent.iter():
        if element.tag.endswith("}" + name):
            return element


def get_attr_wo_ns(element, name):
    for key, value in element.attrib.items():
        if key.endswith("}" + name):
            return value


def get_label(element):
    return get_attr_wo_ns(element, "label")


def find_label(parent, name):
    """find while ignoring namespace"""
    for element in parent.iter():
        if get_label(element) == name:
            return element

def edit_svg():    
    tree = ET.parse(SVG_PATH)
    root = tree.getroot()    
    print(find_label(root, "square"))


def pick_symbol_and_entry(already_picked):
    while True:
        list_index = random.randrange(len(LIST_OF_SYMBOL_ENTRY_LIST_PAIRS))
        symbol, entries = LIST_OF_SYMBOL_ENTRY_LIST_PAIRS[list_index]
        entry = random.choice(entries)
        if entry not in already_picked:
            already_picked.add(entry)
            return symbol, entry


def split_text_box(text):
    if len(text) < 12 or " " not in text:
        return "", text
    spaces = [i for i, c in enumerate(text) if c == " "]
    half_point = len(text) / 2
    middle_space = sorted(spaces, key=lambda x: abs(x-half_point))[0]
    return text[:middle_space], text[middle_space+1:]

def create_svg_from_base(i: int = 0) -> Path:
    svg_path = Path(SVG_PATH)
    new_svg_dir = svg_path.parent / CARD_DIR
    new_svg_path = new_svg_dir / f"{svg_path.stem}_{i:03}{svg_path.suffix}"
    if not new_svg_dir.is_dir():
        new_svg_dir.mkdir()
    with svg_path.open(encoding="utf-8") as fin:
        txt = ""
        already_picked = set()
        for i in range(1,25+1):

            # find next square
            while line := next(fin):
                txt += line
                if SQUARE_STR in line:
                    break

            # pick entry
            symbol, entry = pick_symbol_and_entry(already_picked)
            print(f'{i:2}  {symbol.name:8}  {entry}')
            text1, text2 = split_text_box(entry)
            print(f'  "{text1}"')
            print(f'  "{text2}"')

            # remove unwanted symbols
            while line := next(fin):
                if TEXT_TAG_STR in line:
                    txt += line
                    break
                if WORLD_STR in line and symbol != Symbol.WORLD:
                    txt += line.replace(FILL_STR, BLANK_STR)
                elif OUTFIT_STR in line and symbol != Symbol.OUTFIT:
                    txt += line.replace(FILL_STR, BLANK_STR)
                elif LOCATION_STR in line and symbol != Symbol.LOCATION:
                    txt += line.replace(FILL_STR, BLANK_STR)
                else:
                    txt += line

            # update line 1
            while line := next(fin):
                if LINE1_STR in line:
                    break
                txt += line
            txt += line.replace(LINE1_STR, text1)

            # update line 1
            while line := next(fin):
                if LINE2_STR in line:
                    break
                txt += line
            txt += line.replace(LINE2_STR, text2)

        # get the rest
        try:
            while line := next(fin):
                txt += line
        except StopIteration:
            pass
        new_svg_path.write_text(txt)
    return new_svg_path


def convert_svg_to_pdf(svg_path):
    # inkscape document.svg --export-type=pdf --export-filename document.pdf
    pdf_path = f"{svg_path.parent / svg_path.stem}.pdf"
    subprocess.run([
        "inkscape",
        f"--export-filename={pdf_path}",
        f"{svg_path}"
    ])
    return pdf_path


def merge_pdf_files(pdf_path_list, merge_path):
    merger = PdfWriter()
    for pdf_path in pdf_path_list:
        merger.append(pdf_path)
    merger.write(merge_path)
    merger.close() 


if __name__ == "__main__":
    pdf_path_list = []
    for i in range(100):
        svg_path = create_svg_from_base(i)
        pdf_path = convert_svg_to_pdf(svg_path)
        pdf_path_list.append(pdf_path)
    merge_pdf_files(pdf_path_list, MERGED_PATH)
    print("Done.")
