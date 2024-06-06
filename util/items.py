
import base64
import gzip
import io
import json
from nbtlib import Compound


def decode_nbt(auction: dict) -> dict:
    """
    Decode => Decompress => Warp in io.BytesIO to parse the Base64-encoded data

    :param: auction - Auction data containing the item information
    :return: Parsed NBT data as a Compound object
    """

    encoded_data = auction['item_bytes']
    decoded_data = base64.b64decode(encoded_data)
    decompressed_data = gzip.decompress(decoded_data)
    return Compound.parse(io.BytesIO(decompressed_data))


def parse_item(items: dict, auction: dict) -> None:
    # Decode NBT Data
    nbt_object = decode_nbt(auction)
    tag = nbt_object['']['i'][0]['tag']
    extra_attributes = tag['ExtraAttributes']

    # Item ID Handling
    item_id = str(extra_attributes.get('id'))
    if item_id == "PET":
        pet_info = json.loads(nbt_object['']['i'][0]['tag']['ExtraAttributes']['petInfo'])
        item_id = f'{pet_info["tier"]}_{pet_info["type"]}'
    elif item_id == "RUNE":
        runes = nbt_object['']['i'][0]['tag']['ExtraAttributes']['runes']
        runeKey, runeValue = next(iter(runes.items()))
        item_id = f"{runeKey}_{int(runeValue)}"
    current = items.get(item_id)

    # Item Cost Handling
    item_bin = auction['starting_bid']
    item = {'lbin': item_bin if current is None else min(item_bin, current.get('lbin'))}

    # Pet Level Handling
    if extra_attributes.get('petInfo') is not None:
        item['levels'] = {} if current is None else current.get('levels', {})
        pet_level = tag['display']['Name'].split(' ')[1][0:-1]
        item['levels'][pet_level] = min(item_bin, item['levels'].get(pet_level, item_bin))

    # Attributes Handling
    attributes = extra_attributes.get('attributes')
    if attributes is not None:
        item['attributes'] = {} if current is None else current.get('attributes', {})
        attribute_keys = sorted(attributes.keys())
        check_combo = True

        # Get lbin single attribute
        for attribute in attribute_keys:
            tier = attributes[attribute]
            if tier > 5:
                check_combo = False
            attribute_cost = item_bin / (2 ** (tier - 1))
            if attribute_cost <= item['attributes'].get(attribute, attribute_cost):
                item['attributes'][attribute] = attribute_cost

            # Set Kuudra Armor Attributes
            update_kuudra_piece(items, item_id, attribute, attribute_cost)

        # Get lbin attribute combination
        item_combos = {} if current is None else current.get('attribute_combos', {})
        if check_combo and len(attribute_keys) > 1:
            attribute_combo = ' '.join(attribute_keys)
            item_combos[attribute_combo] = min(item_bin, item_combos.get(attribute_combo, item_bin))
        if item_combos:
            item['attribute_combos'] = item_combos

    # Set Item
    items[item_id] = item


def update_kuudra_piece(items: dict, item_id: str, attribute: str, attribute_cost: float) -> None:
    """
    Parses Kuudra item into specific piece data to add to API.

    :param items: Auction items object to be sent to API.
    :param item_id: Name of item.
    :param attribute: Name of attribute.
    :param attribute_cost: Total value of attribute.
    """
    KUUDRA_PIECES = {'FERVOR', 'AURORA', 'TERROR', 'CRIMSON', 'HOLLOW', 'MOLTEN'}
    item_ids = item_id.split('_')

    if item_ids[0] in KUUDRA_PIECES:
        armor_piece = items.setdefault(item_ids[1], {'attributes': {}})

        # set individual attribute price
        attributes = armor_piece['attributes']
        attributes[attribute] = min(attributes.get(attribute, attribute_cost), attribute_cost)
