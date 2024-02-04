import requests as rq
import json
import os
import pickle
from datetime import datetime
from dotenv import load_dotenv
from util.items import LIMITED
from util.functions import decode_nbt, update_kuudra_piece, is_within_percentage, send_data

AUCTION_URL = 'https://api.hypixel.net/v2/skyblock/auctions_ended'
now = datetime.now().timestamp()


def get_sold_auction(items: dict) -> None:
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
                if attribute_cost <= current_cost:
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
                    current_cost = item_combos.get(attribute_combo, item_bin)
                    if item_bin <= current_cost:
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


def get_items() -> dict:
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


def save_items(items: dict) -> None:
    with open(f'data/sold/auction', 'wb') as file:
        pickle.dump(items, file)


def parse_obj(obj, seconds_frame):
    keys = list(obj.keys())
    for key in keys:
        if now - obj[key].get('timestamp', now) > seconds_frame:
            del obj[key]
        else:
            obj[key]['lbin'] += 1_000


def parse_items(items: dict) -> None:
    week_seconds = 604_800
    keys = list(items.keys())

    for key in keys:
        item = items[key]
        current_lbin = item.get('lbin', 0)

        # parse pricing
        if current_lbin > 100_000_000:
            continue
        elif now - item.get('timestamp', now) > week_seconds:
            del items[key]
        elif current_lbin != 0:
            item['lbin'] += 1_000

        # parse attribute pricing
        parse_obj(item.get('attributes', {}), week_seconds)
        parse_obj(item.get('attribute_combos', {}), week_seconds)


def clean_obj(obj: dict) -> None:
    keys = list(obj.keys())
    for key in keys:
        key_lbin = obj[key]['lbin']
        del obj[key]
        obj[key] = key_lbin


def clean_items(items: dict) -> None:
    for key in items:
        item = items[key]
        if 'timestamp' in item:
            del item['timestamp']

        # remove attribute timestamps
        clean_obj(item.get('attributes', {}))
        clean_obj(item.get('attribute_combos', {}))


def merge_current(items: dict) -> None:
    """
    Merges sold auction data with current auction data to override old

    :param items: Sold auction items data.
    """

    # Merge with current lbin auctions
    with open(f'data/active/auction', 'rb') as file:
        data = pickle.load(file)

        for key in data:
            if key in items and items[key].get('lbin', 0) * 5 >= data[key].get('lbin', 0):
                continue

            items[key] = data[key]
            items[key]['timestamp'] = now

            # set timestamp of attributes
            if 'attributes' in items[key]:
                attributes = items[key]['attributes']
                new_attributes = {}
                for attribute in attributes:
                    new_attributes[attribute] = {}
                    new_attributes[attribute]['lbin'] = attributes[attribute]
                    new_attributes[attribute]['timestamp'] = now

                items[key]['attributes'] = new_attributes

    # Finally merge with hard coded items
    for key in LIMITED:
        if key in items and items[key].get('lbin', 0) * 5 >= LIMITED[key]:
            continue

        items[key] = {
            'lbin': LIMITED[key],
            'timestamp': now
        }


if __name__ == "__main__":
    load_dotenv()
    KEY = os.getenv('KEY')

    # Get data to send
    lbin = get_items()
    parse_items(lbin)
    get_sold_auction(lbin)
    merge_current(lbin)
    save_items(lbin)
    clean_items(lbin)

    # Send to API
    send_data(os.getenv('AUCTION_URL'), {'items': lbin}, KEY)
