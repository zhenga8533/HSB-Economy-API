import base64
import gzip
import io
import json
from datetime import datetime
from nbtlib import Compound
from util.functions import *


def decode_nbt(auction: dict) -> dict:
    """
    Decode => Decompress => Warp in io.BytesIO to parse the Base64-encoded data

    :param: auction - Auction data containing the item information
    :return: Parsed NBT data as a Compound object
    """

    encoded_data = auction["item_bytes"]
    decoded_data = base64.b64decode(encoded_data)
    decompressed_data = gzip.decompress(decoded_data)
    return Compound.parse(io.BytesIO(decompressed_data))


def update_kuudra_piece(items: dict, item_id: str, attribute: str, attribute_cost: float) -> None:
    """
    Parses Kuudra item into specific piece data to add to API.

    :param items: Auction items object to be sent to API.
    :param item_id: Name of item.
    :param attribute: Name of attribute.
    :param attribute_cost: Total value of attribute.
    """

    KUUDRA_PIECES = {"FERVOR", "AURORA", "TERROR", "CRIMSON", "HOLLOW", "MOLTEN"}
    item_ids = item_id.split("_")

    if item_ids[0] in KUUDRA_PIECES:
        armor_piece = items.setdefault(item_ids[1], {"attributes": {}})

        # set individual attribute price
        attributes = armor_piece["attributes"]
        current_cost = attributes[attribute]["lbin"] if attribute in attributes else attribute_cost

        if attribute_cost <= current_cost:
            attributes[attribute] = {"lbin": attribute_cost, "timestamp": datetime.now().timestamp()}
        elif within_percent(current_cost, attribute_cost, 5):
            attributes[attribute]["timestamp"] = datetime.now().timestamp()


def parse_item(items: dict, auction: dict) -> None:
    """
    Parses auction item data and updates the provided 'items' dictionary with the item information.

    :param items: A dictionary containing information about items, where keys are item IDs.
    :param auction: Auction data containing the item information.
    """

    WEEK_SECONDS = 604_800
    now = datetime.now().timestamp()

    # Decode NBT Data
    nbt_object = decode_nbt(auction)
    tag = nbt_object[""]["i"][0]["tag"]
    extra_attributes = tag["ExtraAttributes"]

    # Item ID Handling
    item_id = str(extra_attributes.get("id"))
    if item_id == "PET":
        pet_info = json.loads(nbt_object[""]["i"][0]["tag"]["ExtraAttributes"]["petInfo"])
        item_id = f'{pet_info["tier"]}_{pet_info["type"]}'
    elif item_id == "RUNE":
        runes = nbt_object[""]["i"][0]["tag"]["ExtraAttributes"]["runes"]
        runeKey, runeValue = next(iter(runes.items()))
        item_id = f"{runeKey}_{int(runeValue)}"
    current = items.get(item_id)

    # Item Cost Handling
    item_bin = auction.get("price", auction.get("starting_bid", 0))
    lbin = float("inf") if current is None else current.get("lbin")
    item_base = {"lbin": item_bin, "timestamp": now}

    if check_replace(current, item_bin, now) or item_bin < lbin:
        item = item_base
    else:
        item = {"lbin": lbin, "timestamp": current.get("timestamp")}

    # Pet Level Handling
    if extra_attributes.get("petInfo") is not None:
        item["levels"] = {} if current is None else current.get("levels", {})
        pet_level = tag["display"]["Name"].split(" ")[1][0:-1]
        current_level = item["levels"].get(pet_level, item_base)

        if check_replace(current_level, item_bin, now):
            item["levels"][pet_level] = {"lbin": item_bin, "timestamp": now}

    # Attributes Handling
    attributes = extra_attributes.get("attributes")
    if attributes is not None:
        item["attributes"] = {} if current is None else current.get("attributes", {})
        attribute_keys = sorted(attributes.keys())
        check_combo = True

        # Get lbin single attribute
        for attribute in attribute_keys:
            tier = attributes[attribute]
            if tier > 5:
                check_combo = False
            attribute_cost = item_bin / (2 ** (tier - 1))
            current_cost = (
                attribute_cost if attribute not in item["attributes"] else item["attributes"][attribute]["lbin"]
            )

            if attribute_cost <= current_cost:
                item["attributes"][attribute] = {
                    "lbin": attribute_cost,
                    "timestamp": now,
                }

            # Set Kuudra Armor Attributes
            update_kuudra_piece(items, item_id, attribute, attribute_cost)

        # Get lbin attribute combination
        item_combos = {} if current is None else current.get("attribute_combos", {})
        if check_combo and len(attribute_keys) > 1:
            attribute_combo = " ".join(attribute_keys)
            current_cost = item_bin if attribute_combo not in item_combos else item_combos[attribute_combo]["lbin"]

            if item_bin <= current_cost:
                item_combos[attribute_combo] = {"lbin": item_bin, "timestamp": now}
        if item_combos:
            item["attribute_combos"] = item_combos

    # Set Item
    items[item_id] = item
