import json
import os
import pickle
import requests as rq
from datetime import datetime
from dotenv import load_dotenv
from util.functions import send_data
from util.items import parse_item


def get_items() -> dict:
    """
    Retrieves item data from the stored file or returns an empty dictionary if no data is available.

    :return: A dictionary containing information about items, where keys are item IDs.
    """

    # Check for data directory and files
    if not os.path.exists("data/auction"):
        os.makedirs("data/auction")

    # Check for auction file
    if not os.path.isfile("data/auction/sold"):
        return {}

    # Load auction data
    with open(f"data/auction/sold", "rb") as file:
        return pickle.load(file)


def parse_items(items: dict) -> None:
    """
    Parses and updates the provided 'items' dictionary, removing entries with outdated timestamps,
    incrementing 'lbin' values, and applying similar updates to attribute and attribute_combos dictionaries.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    INCREMENT = 2_500

    for key in items:
        item = items[key]

        # parse pricing
        if item.get("lbin", 0) != 0:
            item["lbin"] += INCREMENT

        # Parse attribute pricing
        if "attributes" in item:
            parse_items(item["attributes"])
        if "attribute_combos" in item:
            parse_items(item["attribute_combos"])


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


def merge_current(items: dict) -> None:
    """
    Merges sold auction data with current auction data to override old.

    :param: items - Sold auction items data.
    :return: None
    """

    now = datetime.now().timestamp()

    with open(f"data/auction/active", "rb") as file:
        active = pickle.load(file)

        for key in active:
            timestamp = items[key].get("timestamp", now) if key in items else now
            currPrice = items[key].get("lbin", 0) if key in items else 0
            binPrice = active[key].get("lbin", 0)

            if key in items and currPrice * 5 >= binPrice > currPrice and timestamp + 604_800 < now:
                continue

            items[key] = active[key]
            items[key]["timestamp"] = now

        # TBD: Add limited items


def save_items(items: dict, log: bool = False) -> None:
    """
    Saves the provided item data to the specified file.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    with open(f"data/auction/sold", "wb") as file:
        pickle.dump(items, file)

    if log:
        with open("data/json/sold.json", "w") as file:
            json.dump(items, file, indent=4)


def clean_items(items: dict, low=0) -> None:
    """
    Cleans the provided 'items' dictionary by removing 'timestamp' entries and cleaning attribute dictionaries.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :param: low - Lowest cost item can be otherwise it is deleted.
    :return: None
    """

    keys = list(items.keys())

    for key in keys:
        item = items[key]

        # Remove timestamp
        if "timestamp" in item:
            del item["timestamp"]

        # Remove low items
        if items[key].get("lbin", 0) < low:
            del items[key]

        # Clean attributes
        if "attributes" in item:
            clean_items(item["attributes"])
        if "attribute_combos" in item:
            clean_items(item["attribute_combos"], low=10_000_000)


def send_items(items: dict) -> None:
    """
    Sends the provided 'items' data using an API call.

    :param: items - A dictionary containing lbin information about items.
    :return: None
    """

    KEY = os.getenv("KEY")
    send_data(os.getenv("AUCTION_URL"), {"items": items}, KEY)


if __name__ == "__main__":
    load_dotenv()
    LOG = os.getenv("LOG") == "True"
    ah = get_items()

    # Fetch data
    parse_items(ah)
    get_sold_auction(ah)
    merge_current(ah)

    # Save and send data
    save_items(ah, LOG)
    clean_items(ah)
    if LOG:
        print(ah)
    # send_items(ah)
