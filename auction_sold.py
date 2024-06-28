import os
import pickle
import requests as rq
from datetime import datetime
from dotenv import load_dotenv
from util.functions import *
from util.items import parse_item


def get_items() -> dict:
    """
    Retrieves item data from the stored file or returns an empty dictionary if no data is available.

    :return: A dictionary containing information about items, where keys are item IDs.
    """

    # Check for auction file
    os.makedirs("data/pickle", exist_ok=True)
    if not os.path.isfile("data/pickle/sold"):
        return {}

    # Load auction data
    with open(f"data/pickle/sold", "rb") as file:
        return pickle.load(file)


def get_sold_auction(items: dict) -> None:
    """
    Fetches auction data and processes items lbin data.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    # Get auction data
    response = rq.get("https://api.hypixel.net/v2/skyblock/auctions_ended")
    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return

    # Parse auction data
    data = response.json()
    for auction in data["auctions"]:
        parse_item(items, auction)


def merge_auctions(items: dict) -> None:
    """
    Merges sold auction data with current auction data to override old.

    :param: items - Sold auction items data.
    :return: None
    """

    now = datetime.now().timestamp()

    with open(f"data/pickle/active", "rb") as file:
        active = pickle.load(file)

        for key in active:
            timestamp = items[key].get("timestamp", now) if key in items else now
            currPrice = items[key].get("lbin", 0) if key in items else 0
            binPrice = active[key].get("lbin", 0)

            if key in items and currPrice * 3 >= binPrice > currPrice and timestamp + 604_800 > now:
                continue

            items[key] = active[key]
            items[key]["timestamp"] = now

    with open(f"data/pickle/limited", "rb") as file:
        limited = pickle.load(file)

        for key in limited:
            timestamp = items[key].get("timestamp", now) if key in items else now

            if key in items and timestamp + 604_800 > now:
                continue

            items[key] = limited[key]
            items[key]["timestamp"] = now


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    INCREMENT = int(os.getenv("INCREMENT"))
    KEY = os.getenv("KEY")
    LOG = os.getenv("LOG") == "True"
    URL = os.getenv("AUCTION_URL")

    # Fetch data
    ah = get_items()
    increment_data(data=ah, increment=INCREMENT)
    get_sold_auction(items=ah)
    merge_auctions(items=ah)

    # Save and send data
    save_data(data=ah, name="sold", log=LOG)
    clean_data(ah)
    send_data(url=URL, data=ah, key=KEY)
