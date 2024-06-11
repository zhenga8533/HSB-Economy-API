
import base64
import gzip
import io
import json
from datetime import datetime
from nbtlib import Compound
from util.functions import check_replace


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
            current_cost = attributes[attribute]['lbin'] if attribute in attributes else attribute_cost
            attributes[attribute] = min(attributes.get(attribute, attribute_cost), attribute_cost)

            if attribute_cost <= current_cost:
                attributes[attribute] = {'lbin': attribute_cost, 'timestamp': datetime.now().timestamp()}
            elif is_within_percentage(current_cost, attribute_cost, 5):
                attributes[attribute]['timestamp'] = datetime.now().timestamp()


    WEEK_SECONDS = 604_800
    now = datetime.now().timestamp()

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
    item_bin = auction.get('price', auction.get('starting_bid', 0))
    lbin = float('inf') if current is None else current.get('lbin')
    item_base = {'lbin': item_bin, 'timestamp': now}

    if check_replace(current, item_bin, now) or item_bin < lbin:
        item = item_base
    else:
        item = {'lbin': lbin, 'timestamp': current.get('timestamp')}

    # Pet Level Handling
    if extra_attributes.get('petInfo') is not None:
        item['levels'] = {} if current is None else current.get('levels', {})
        pet_level = tag['display']['Name'].split(' ')[1][0:-1]
        current_level = item['levels'].get(pet_level, item_base)

        if check_replace(current_level, item_bin, now):
            item['levels'][pet_level] = {
                'lbin': item_bin,
                'timestamp': now
            }

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
            update_kuudra_piece(items, item_id, attribute, attribute_cost, False)

        # Get lbin attribute combination
        item_combos = {} if current is None else current.get('attribute_combos', {})
        if check_combo and len(attribute_keys) > 1:
            attribute_combo = ' '.join(attribute_keys)
            item_combos[attribute_combo] = min(item_bin, item_combos.get(attribute_combo, item_bin))
        if item_combos:
            item['attribute_combos'] = item_combos

    # Set Item
    items[item_id] = item


def parse_auction(items: dict, auction: dict) -> None:
    def update_kuudra_piece(items: dict, item_id: str, attribute: str, attribute_cost: float) -> bool:
        """
        Parses Kuudra item into specific piece data to add to API.

        :param: items - Auction items object to be sent to API.
        :param: item_id - Name of item.
        :param: attribute - Name of attribute.
        :param: attribute_cost - Total value of attribute.
        :return: True if piece is a Kuudra piece otherwise False.
        """
        KUUDRA_PIECES = {'FERVOR', 'AURORA', 'TERROR', 'CRIMSON', 'HOLLOW', 'MOLTEN'}
        item_ids = item_id.split('_')

        if item_ids[0] in KUUDRA_PIECES:
            armor_piece = items.setdefault(item_ids[1], {'attributes': {}})

            # set individual attribute price
            attributes = armor_piece['attributes']
            current_cost = attributes[attribute]['lbin'] if attribute in attributes else attribute_cost
            if attribute_cost <= current_cost:
                attributes[attribute] = {'lbin': attribute_cost, 'timestamp': datetime.now().timestamp()}
            elif is_within_percentage(current_cost, attribute_cost, 5):
                attributes[attribute]['timestamp'] = datetime.now().timestamp()

            return True
        return False

    WEEK_SECONDS = 604_800
    now = datetime.now().timestamp()

    # Get Item ID
    nbt_object = decode_nbt(auction)
    extra_attributes = nbt_object['']['i'][0]['tag']['ExtraAttributes']

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
    item_bin = auction.get('price', auction.get('starting_bid', 0))
    lbin = float('inf') if current is None else current.get('lbin')
    timestamp = auction.get('timestamp', datetime.now().timestamp()) / 1000 if current is None or is_within_percentage(item_bin, lbin, 5) \
        or item_bin < lbin else current.get('timestamp')
    item = {'lbin': item_bin if current is None else min(item_bin, current.get('lbin')),
            'timestamp': timestamp}
    if timestamp + WEEK_SECONDS > now:
        item = {'lbin': item_bin, 'timestamp': now}

    # Attributes Handling
    attributes = extra_attributes.get('attributes')
    item['attributes'] = {} if current is None else current.get('attributes') or {}

    if attributes is not None:
        item_attributes = item['attributes']
        attribute_keys = sorted(attributes.keys())
        check_combo = True
        is_kuudra_piece = False

        # Get lbin single attribute
        for attribute in attribute_keys:
            tier = attributes[attribute]
            if tier > 5:
                check_combo = False
            attribute_cost = item_bin / (2 ** (tier - 1))
            current_cost = item_attributes[attribute]['lbin'] if attribute in item_attributes else attribute_cost

            if attribute_cost <= current_cost or item_attributes[attribute]['timestamp'] + WEEK_SECONDS > now:
                item_attributes[attribute] = {'lbin': attribute_cost, 'timestamp': now}
            elif is_within_percentage(current_cost, attribute_cost, 5):
                item_attributes[attribute]['timestamp'] = now

            # Set Kuudra Armor Attributes
            is_kuudra_piece = update_kuudra_piece(items, item_id, attribute, attribute_cost)

        # Get lbin attribute combination if value > X (to check for Kuudra god roll)
        if is_kuudra_piece:
            item_combos = current.get('attribute_combos', {}) if current and 'attribute_combos' in current else {}
            if check_combo and len(attribute_keys) > 1:
                attribute_combo = ' '.join(attribute_keys)
                current_cost = item_combos[attribute_combo]['lbin'] if attribute_combo in item_combos else item_bin

                if item_bin <= current_cost or item_combos[attribute_combo]['timestamp'] + WEEK_SECONDS > now:
                    item_combos[attribute_combo] = {'lbin': item_bin, 'timestamp': now}
                elif is_within_percentage(current_cost, item_bin, 5):
                    item_combos[attribute_combo]['timestamp'] = now
            if item_combos:
                item['attribute_combos'] = item_combos

    # Delete attribute variable for no attribute items
    if item['attributes'] == {}:
        del item['attributes']

    # Set Item
    items[item_id] = item
