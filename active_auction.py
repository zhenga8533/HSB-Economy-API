import json
import os
import pickle
import requests as rq
from util.items import parse_item


def get_active_auction(items: dict, page: int, log: bool=False) -> None:
    """
    Fetch auction data and process items lbin data.

    :param: items - Item data object
    :param: page - Page number of the auction data
    :return: None
    """

    # Get Auction Data
    response = rq.get('https://api.hypixel.net/v2/skyblock/auctions', params={'page': page})
    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return
    data = response.json()

    # Loop through Auction Data
    if log:
        print(f"Auction Looping ({page + 1}/{data['totalPages']})", end='\r')
    for auction in data['auctions']:
        if not auction['bin']:
            continue

        parse_item(items, auction)
    if page + 1 < data['totalPages']:
        get_active_auction(items, page + 1, log)
    elif log:
        print('Auction Process Complete!')


def save_items(items: dict, log: bool=False) -> None:
    """
    Manages the provided 'items' dictionary, saving it to a file for persistence.
    Saves the provided 'items' dictionary to files, managing daily and weekly averages for persistence.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    # Check for data directory and files
    if not os.path.exists('data/auction'):
        os.makedirs('data/auction')

    # Save items
    with open(f'data/auction/active', 'wb') as file:
        pickle.dump(items, file)

    if log:
        # Save items as JSON
        with open('data/auction/active.json', 'w') as file:
            json.dump(items, file, indent=4)


if __name__ == '__main__':
    ah = {}
    log = True

    # Get data to send
    get_active_auction(ah, 0, log)
    save_items(ah, log)
