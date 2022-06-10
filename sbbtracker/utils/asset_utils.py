import copy
import json
import logging
import sys
import os
from collections import namedtuple
from pathlib import Path

import pandas as pd

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    application_path = Path(sys._MEIPASS)
else:
    application_path = Path(__file__).parent.parent

def get_asset(asset_name: str):
    return str(application_path.joinpath(f"../assets/{asset_name}"))


# headers:
# Id|InPool|Name|Cost|Level|Attack|Health|Game Text|Golden or regular|Type|Subtypes|Keywords
with open(get_asset("CardFile.txt"), "r") as card_file:
    cardfile_df = pd.read_csv(card_file, delimiter='|')
    content_id_lookup = {}
    for index, row in cardfile_df.iterrows():
        content_id_lookup[str(index)] = { "Id": row["Id"], "Name": row["Name"] }

def get_card_art_name(template_id: str, is_golden: bool):
    """
    Map the content ID to the card to prevent issues with skins/renames.
    :param template_id: content_id of the card, e.g. SBB_HERO_GWEN
    :param is_golden: is the card golden
    :return: the base card art name
    """
    try:
        return content_id_lookup.get(str(int(template_id) - int(is_golden)))["Id"]
    except TypeError:
        logging.error(template_id)
        return ""


def get_card_name(template_id: str, is_golden=False):
    try:
        return content_id_lookup.get(str(int(template_id) - int(is_golden)))["Name"]
    except TypeError:
        logging.error(template_id)
        return ""


def get_num_heroes():
    hero_list = [v for v in content_id_lookup.values() if v['Id'].startswith("SBB_HERO") and v['Name'] != "Big Bad Wolf"]
    name_list = []
    for hero in hero_list:
        name = hero["Name"]
        if name not in name_list:
            name_list.append(name)
    return len(name_list)

def get_card_path(content_id: str, is_golden: bool):
    """
    Gets the path for the card asset
    :param content_id: the content id of the card, e.g. SBB_HERO_GWEN
    :param is_golden: if the card is golden or not
    :return: the path card art if it exists, otherwise path to the blank resource
    """
    cards_path = application_path.joinpath("../cards/")
    # what the fuck is this
    actually_is_golden = is_golden if isinstance(is_golden, bool) else is_golden == "True"
    input_content_id = get_card_art_name(content_id, actually_is_golden)
    asset_name = input_content_id
    path = cards_path.joinpath(asset_name.replace("'", "_") + ".png")
    if not path.exists() or asset_name == "empty":
        path = Path("../../assets/").joinpath("Empty.png")
    return str(path)


def replace_template_ids(state):
    copied = copy.deepcopy(state)
    for playerid in copied:
        for character in copied[playerid]:
            templateid = character.content_id
            is_golden = character.is_golden if hasattr(character, "is_golden") else False
            actually_is_golden = is_golden if isinstance(is_golden, bool) else is_golden == "True"
            character.content_id = get_card_art_name(templateid, actually_is_golden)
            if hasattr(character, "health") and character.health <= 0:
                character.content_id = ""
    return copied

