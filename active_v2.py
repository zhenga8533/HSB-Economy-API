import requests as rq
import json
import os
import pickle
from util.functions import decode_nbt

AUCTION_URL = 'https://api.hypixel.net/v2/skyblock/auctions'


def get_active_auction(items: dict, page: int, log: bool=False) -> None:
    """
    Fetch auction data and process items lbin data.

    :param: items - Item data object
    :param: page - Page number of the auction data
    :return: None
    """

    # Get Auction Data
    response = rq.get(AUCTION_URL, params={'page': page})
    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return
    data = response.json()

    # Loop through Auction Data
    if log:
        print(f"Auction Looping ({page + 1}/{data['totalPages']})")
    for auction in data["auctions"]:
        if not auction['bin']:
            continue

        # Decode NBT Data
        nbt_object = decode_nbt(auction)
        tag = nbt_object['']['i'][0]['tag']
        extra_attributes = tag['ExtraAttributes']

        # Item ID Handling
        item_id = str(extra_attributes.get('id'))
        if item_id == "PET":
            pet_info = json.loads(nbt_object['']['i'][0]['tag']['ExtraAttributes']['petInfo'])

            
            level = tag['display']['Name'].split(' ')[1][0:-1]


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
        item['attributes'] = {} if current is None else current.get('attributes') or {}

        if attributes is not None:
            attribute_keys = sorted(attributes.keys())
            check_combo = True
            is_kuudra_piece = False

            # Get lbin single attribute
            for attribute in attribute_keys:
                tier = attributes[attribute]
                if tier > 5:
                    check_combo = False
                attribute_cost = item_bin / (2 ** (tier - 1))
                if attribute_cost <= item['attributes'].get(attribute, attribute_cost):
                    item['attributes'][attribute] = attribute_cost

                # Set Kuudra Armor Attributes
                is_kuudra_piece = update_kuudra_piece(items, item_id, attribute, attribute_cost)

            # Get lbin attribute combination if value > X (to check for Kuudra god roll)
            if is_kuudra_piece:
                item_combos = current.get('attribute_combos', {}) if current and 'attribute_combos' in current else {}
                if check_combo and len(attribute_keys) > 1:
                    attribute_combo = ' '.join(attribute_keys)
                    item_combos[attribute_combo] = min(item_bin, item_combos.get(attribute_combo, item_bin))
                if item_combos:
                    item['attribute_combos'] = item_combos

        # Delete attribute variable for no attribute items
        if item['attributes'] == {}:
            del item['attributes']

        # Set Item
        items[item_id] = item

    if page + 1 < data['totalPages']:
        return
        get_active_auction(items, page + 1)
    else:
        save_items(items)
        if log:
            print('Auction Process Complete!')


def update_kuudra_piece(items: dict, item_id: str, attribute: str, attribute_cost: float) -> bool:
    """
    Parses Kuudra item into specific piece data to add to API.

    :param items: Auction items object to be sent to API.
    :param item_id: Name of item.
    :param attribute: Name of attribute.
    :param attribute_cost: Total value of attribute.
    :return: True if piece is a Kuudra piece otherwise False.
    """
    KUUDRA_PIECES = {'FERVOR', 'AURORA', 'TERROR', 'CRIMSON', 'HOLLOW', 'MOLTEN'}
    item_ids = item_id.split('_')

    if item_ids[0] in KUUDRA_PIECES:
        armor_piece = items.setdefault(item_ids[1], {'attributes': {}})

        # set individual attribute price
        attributes = armor_piece['attributes']
        attributes[attribute] = min(attributes.get(attribute, attribute_cost), attribute_cost)

        return True
    return False


def save_items(items: dict) -> None:
    """
    Manages the provided 'items' dictionary, saving it to a file for persistence.
    Saves the provided 'items' dictionary to files, managing daily and weekly averages for persistence.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    # Check for data directory and files
    if not os.path.exists('data/active'):
        os.makedirs('data/active')

    # Save items
    with open(f'data/active/auction', 'wb') as file:
        pickle.dump(items, file)


if __name__ == '__main__':
    # Get data to send
    ah = {}
    get_active_auction(ah, 0, True)
