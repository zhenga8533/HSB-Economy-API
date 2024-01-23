import requests as rq
import json
import os
import pickle
from datetime import datetime
from dotenv import load_dotenv
from auction_api.util.functions import decode_nbt, update_kuudra_piece, average_objects, is_within_percentage

AUCTION_URL = 'https://api.hypixel.net/v2/skyblock/auctions_ended'


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
        item_attributes = item['attributes']
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
                current_cost = item_attributes[attribute]['lbin'] if attribute in item_attributes else attribute_cost
                if attribute_cost <= current_cost:
                    item_attributes[attribute] = {'lbin': attribute_cost, 'timestamp': datetime.now().timestamp()}
                elif is_within_percentage(current_cost, attribute_cost, 5):
                    item_attributes[attribute]['timestamp'] = datetime.now().timestamp()

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


def parse_items(items: dict) -> None:
    now = datetime.now().timestamp()
    day_seconds = 86400

    # Create a list to store keys for deletion
    keys_to_delete = []

    # Iterate over a copy of the keys to avoid dictionary size change during iteration
    for key in items.keys():
        item = items[key]
        current_lbin = item.get('lbin', 0)

        if current_lbin > 100_000_000:
            continue
        elif now - item.get('timestamp', now) > day_seconds:
            keys_to_delete.append(key)
        elif current_lbin != 0:
            item['lbin'] += 1_000

    # Delete the keys after the iteration is complete
    for key in keys_to_delete:
        del items[key]


if __name__ == "__main__":
    load_dotenv()
    KEY = os.getenv('KEY')

    # Get data to send
    lbin = get_items()
    parse_items(lbin)
    get_sold_auction(lbin)
    save_items(lbin)
    print(lbin)

    # Send to API
    # send_data(os.getenv('AUCTION_URL'), {'items': auction}, KEY)
