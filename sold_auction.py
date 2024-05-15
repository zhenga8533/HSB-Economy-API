import requests as rq
import json
import os
import pickle
from datetime import datetime
from dotenv import load_dotenv
from util.items import LIMITED
from util.functions import decode_nbt, is_within_percentage, send_data

AUCTION_URL = 'https://api.hypixel.net/v2/skyblock/auctions_ended'
INCREMENT = 2_500
WEEK_SECONDS = 604_800
now = datetime.now().timestamp()


def get_sold_auction(items: dict) -> None:
    """
    Fetches data from the specified AUCTION_URL, processes and updates the provided 'items' dictionary
    with information about sold auctions.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    response = rq.get(AUCTION_URL)

    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return

    data = response.json()
    for auction in data["auctions"]:
        if not auction['bin']:
            continue

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
        item_bin = auction['price']
        current_lbin = float('inf') if current is None else current.get('lbin')
        timestamp = auction['timestamp'] / 1000 if current is None or is_within_percentage(item_bin, current_lbin, 5) \
            or item_bin < current_lbin else current.get('timestamp')
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

    merge_current(items)


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


def get_items() -> dict:
    """
    Retrieves item data from the stored file or returns an empty dictionary if no data is available.

    :return: A dictionary containing information about items, where keys are item IDs.
    """

    # Check for data directory and files
    if not os.path.exists('data/sold'):
        os.makedirs('data/sold')
    if not os.path.isfile('data/sold/auction'):
        with open('data/sold/auction', 'wb') as file:
            pickle.dump({}, file)
            return {}

    # otherwise send current item data
    with open(f'data/sold/auction', 'rb') as file:
        return pickle.load(file)


def parse_obj(obj: dict) -> None:
    """
    Updates the provided dictionary by  incrementing the 'lbin' value for remaining entries.

    :param: obj - A dictionary to be processed, where keys are identifiers and values are dictionaries
                containing 'timestamp' and 'lbin'.
    :return: None
    """

    keys = list(obj.keys())
    for key in keys:
        obj[key]['lbin'] += INCREMENT


def parse_items(items: dict) -> None:
    """
    Parses and updates the provided 'items' dictionary, removing entries with outdated timestamps,
    incrementing 'lbin' values, and applying similar updates to attribute and attribute_combos dictionaries.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    keys = list(items.keys())

    for key in keys:
        item = items[key]
        current_lbin = item.get('lbin', 0)

        # parse pricing
        if current_lbin != 0:
            item['lbin'] += INCREMENT

        # parse attribute pricing
        parse_obj(item.get('attributes', {}))
        parse_obj(item.get('attribute_combos', {}))


def timestamp_obj(obj: dict, var: str) -> None:
    """
    Timestamps the entries in the specified dictionary under the given variable.

    :param: obj - A dictionary to be processed, where keys are identifiers and values are dictionaries.
    :param: var - The variable within the dictionary to be timestamped.
    :return: None
    """

    if var in obj:
        keys = obj[var]
        new_keys = {}
        for key in keys:
            new_keys[key] = {
                'lbin': keys[key],
                'timestamp': now
            }
        obj[var] = new_keys


def merge_current(items: dict) -> None:
    """
    Merges sold auction data with current auction data to override old

    :param: items - Sold auction items data.
    :return: None
    """

    # Merge with current lbin auctions
    with open(f'data/active/auction', 'rb') as file:
        data = pickle.load(file)

        for key in data:
            timestamp = items[key].get('timestamp', 0) if key in items else 0
            currPrice = items[key].get('lbin', 0) if key in items else 0
            binPrice = data[key].get('lbin', 0)

            if key in items and currPrice * 5 >= binPrice > currPrice and timestamp + WEEK_SECONDS < now:
                continue

            items[key] = data[key]
            items[key]['timestamp'] = now

            # set timestamp of attributes
            timestamp_obj(items[key], 'attributes')
            timestamp_obj(items[key], 'attribute_combos')

    # Finally merge with hard coded items

    for key in LIMITED:
        timestamp = items[key].get('timestamp', 0) if key in items else 0
        softPrice = items[key].get('lbin', 0) if key in items else 0
        hardPrice = LIMITED[key]

        if key in items and softPrice * 5 >= hardPrice > softPrice and timestamp + WEEK_SECONDS < now:
            continue

        items[key] = {
            'lbin': LIMITED[key],
            'timestamp': now
        }

    save_items(items)


def save_items(items: dict) -> None:
    """
    Saves the provided item data to the specified file.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    with open(f'data/sold/auction', 'wb') as file:
        pickle.dump(items, file)

    clean_items(items)


def clean_obj(obj: dict, low=0) -> None:
    """
    Cleans the provided dictionary by removing entries and preserving their 'lbin' values.

    :param: obj - A dictionary to be cleaned, where keys are identifiers and values are dictionaries
                containing 'lbin'.
    :param: low - Lowest cost item can be otherwise it is deleted.
    :return: None
    """

    keys = list(obj.keys())
    for key in keys:
        key_lbin = obj[key]['lbin']
        del obj[key]
        if key_lbin > low:
            obj[key] = key_lbin


def clean_items(items: dict) -> None:
    """
    Cleans the provided 'items' dictionary by removing 'timestamp' entries and cleaning attribute dictionaries.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    for key in items:
        item = items[key]
        if 'timestamp' in item:
            del item['timestamp']

        # remove attribute timestamps
        clean_obj(item.get('attributes', {}))
        clean_obj(item.get('attribute_combos', {}), low=10_000_000)

    send_items(items)


def send_items(items: dict) -> None:
    """
    Sends the provided 'items' data using an API call.

    :param: items - A dictionary containing lbin information about items.
    :return: None
    """

    load_dotenv()
    KEY = os.getenv('KEY')
    send_data(os.getenv('AUCTION_URL'), {'items': items}, KEY)


if __name__ == "__main__":
    lbin = get_items()
    parse_items(lbin)
    get_sold_auction(lbin)
