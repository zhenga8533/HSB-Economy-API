import os
import requests as rq
from dotenv import load_dotenv
from util.items import parse_item
from util.functions import *


def get_active_auction(items: dict, log: bool = False) -> None:
    """
    Fetch auction data and process items lbin data.

    :param: items - Item data object
    :param: page - Page number of the auction data
    :param: log - Whether to log the process
    :return: None
    """
    page = 0
    while True:
        response = rq.get("https://api.hypixel.net/v2/skyblock/auctions", params={"page": page})
        if response.status_code != 200:
            print(f"Failed to get data. Status code: {response.status_code}")
            return
        data = response.json()

        if log:
            print(f"Auction Looping ({page + 1}/{data['totalPages']})", end="\r")

        for auction in data["auctions"]:
            if auction["bin"]:
                parse_item(items, auction)

        page += 1
        if page >= data["totalPages"]:
            break

    if log:
        print("Auction Process Complete!")


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    LOG = os.getenv("LOG") == "True"

    # Get data to send
    ah = {}
    get_active_auction(items=ah, log=LOG)
    save_data(data=ah, name="active", log=LOG)
