import requests as rq
import json
import base64
import gzip
import io
from nbtlib import Compound

AUCTION_URL = 'https://api.hypixel.net/skyblock/auctions'
API_URL = 'https://volcaronitee.pythonanywhere.com'
items = {}


def get_auction(page):
    response = rq.get(AUCTION_URL, params={'page': page})

    # Check if the request was successful (status code 200 indicates success)
    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return

    # The API response is usually in JSON format, so you can parse it like this:
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
        current = items.get(item_id)

        # Item Cost Handling
        item_bin = auction['starting_bid']
        item = {'lbin': item_bin if current is None else min(item_bin, current.get('lbin'))}

        # Attributes Handling
        attributes = extra_attributes.get('attributes')
        if attributes is not None:
            item['attributes'] = {} if current is None else current.get('attributes') or {}
            attributes = dict(sorted(attributes.items()))
            for attribute in attributes:
                attribute_cost = item_bin / (2 ** (attributes[attribute] - 1))
                item['attributes'][attribute] = min(attribute_cost, item['attributes'].get(attribute, attribute_cost))
            # attribute_combo = list(attributes.keys())

        # Set Item
        items[item_id] = item
    """
    if page + 1 < data['totalPages']:
        get_auction(page + 1)
    else:
        print(f'Auction Loop Complete!')
    """


# Function to send data via POST request
def send_data(data):
    response = rq.post(API_URL, json=data)
    return response.json()


if __name__ == "__main__":
    get_auction(0)
    response_json = send_data({'items': items})
