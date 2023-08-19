import requests as rq
import json
import base64
import gzip
import io
from nbtlib import Compound

AUCTION_URL = 'https://api.hypixel.net/skyblock/auctions'
items = {}


def decode_nbt(auction):
    """
    Decode and parse the NBT data from the auction item.

    :param auction: Auction data containing the item information
    :return: Parsed NBT data as a Compound object
    """

    encoded_data = auction["item_bytes"]
    decoded_data = base64.b64decode(encoded_data)
    decompressed_data = gzip.decompress(decoded_data)
    return Compound.parse(io.BytesIO(decompressed_data))


def update_kuudra_piece(item_id, attribute, attribute_cost):
    KUUDRA_PIECES = {"FERVOR", "AURORA", "TERROR", "CRIMSON", "HOLLOW", "MOLTEN"}
    item_ids = item_id.split('_')

    if item_ids[0] in KUUDRA_PIECES:
        armor_piece = items.setdefault(item_ids[1], {"attributes": {}})
        armor_piece_attributes = armor_piece["attributes"]
        current_attribute_cost = armor_piece_attributes.get(attribute, attribute_cost)
        armor_piece_attributes[attribute] = min(attribute_cost, current_attribute_cost)


def get_auction(page):
    """
    Fetch auction data and process items lbin data.

    :param page: Page number of the auction data
    """

    response = rq.get(AUCTION_URL, params={'page': page})

    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return

    data = response.json()
    print(f'Auction Looping: {page + 1}/{data.get("totalPages")}')
    for auction in data["auctions"]:
        if not auction['bin']:
            continue

        # Get Item ID
        # Decode => Decompress => Warp in io.BytesIO to parse the Base64-encoded data
        encoded_data = auction["item_bytes"]
        decoded_data = base64.b64decode(encoded_data)
        decompressed_data = gzip.decompress(decoded_data)
        nbt_object = Compound.parse(io.BytesIO(decompressed_data))
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
        item_bin = auction['starting_bid']
        item = {'lbin': item_bin if current is None else min(item_bin, current.get('lbin'))}

        # Attributes Handling
        attributes = extra_attributes.get('attributes')
        if attributes is not None:
            USEFUL_ATTRIBUTES = {
                "breeze", "dominance", "fortitude", "life_regeneration", "lifeline", "magic_find", "mana_pool",
                "mana_regeneration", "mending", "speed", "veteran", "blazing_fortune", "fishing_experience"
            }
            attribute_keys = sorted(attributes.keys() & USEFUL_ATTRIBUTES)

            # Get lbin attributes
            item['attributes'] = {} if current is None else current.get('attributes') or {}
            check_combo = True
            for attribute in attribute_keys:
                tier = attributes[attribute]
                if tier > 5:
                    check_combo = False
                attribute_cost = item_bin / (2 ** (tier - 1))
                if attribute_cost <= item['attributes'].get(attribute, attribute_cost):
                    item['attributes'][attribute] = attribute_cost

                    # Set Kuudra Armor Attributes
                    update_kuudra_piece(item_id, attribute, attribute_cost)

            # Get lbin attribute combination if value > X
            item_combos = current.get('attribute_combos', {}) if current and 'attribute_combos' in current else {}
            if check_combo and len(attribute_keys) > 1:
                attribute_combo = ' '.join(attribute_keys)
                item_combos[attribute_combo] = min(item_bin, item_combos.get(attribute_combo, item_bin))
            if item_combos:
                item['attribute_combos'] = item_combos

        # Set Item
        items[item_id] = item

    if page + 1 < data['totalPages']:
        get_auction(page + 1)
        if page == 0:
            return items
    else:
        print(f'Auction Loop Complete!')
