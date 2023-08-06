import requests as rq
import json
import base64
import gzip
import io
from nbtlib import Compound

AUCTION_URL = 'https://api.hypixel.net/skyblock/auctions'
API_URL = 'https://volcaronitee.pythonanywhere.com'
lbin = {}


def get_auction(page):
    response = rq.get(AUCTION_URL, params={'page': page})

    # Check if the request was successful (status code 200 indicates success)
    if response.status_code == 200:
        # The API response is usually in JSON format, so you can parse it like this:
        data = response.json()
        print(f'Auction Looping: {page + 1}/{data.get("totalPages")}')
        for auction in data["auctions"]:
            if auction['bin']:
                item_cost = auction['starting_bid']

                # Get Item ID
                # Decode => Decompress => Warp in io.BytesIO to parse the Base64-encoded data
                encoded_data = auction["item_bytes"]
                decoded_data = base64.b64decode(encoded_data)
                decompressed_data = gzip.decompress(decoded_data)
                nbt_object = Compound.parse(io.BytesIO(decompressed_data))
                item_id = str(nbt_object['']['i'][0]['tag']['ExtraAttributes']['id'])
                if item_id == "PET":
                    pet_info = json.loads(nbt_object['']['i'][0]['tag']['ExtraAttributes']['petInfo'])
                    item_id = f'{pet_info["tier"]}_{pet_info["type"]}'

                current = lbin.get(item_id)
                lbin[item_id] = item_cost if current is None else min(item_cost, lbin.get(item_id))
        if page + 1 < data['totalPages']:
            get_auction(page + 1)
        else:
            print(f'Auction Loop Complete!')
    else:
        print(f"Failed to get data. Status code: {response.status_code}")
        data = None
    return data


# Function to send data via POST request
def send_data(data):
    response = rq.post(API_URL, json=data)
    return response.json()


if __name__ == "__main__":
    get_auction(0)

    data_to_send = {'lbin': lbin}  # Replace with your desired data
    response_json = send_data(data_to_send)
