import os
import pickle
import requests as rq
import sys
from datetime import datetime
from dotenv import load_dotenv
from util.functions import *
from util.items import parse_item


DATA_DIR = "data/pickle"
SOLD_FILE = f"{DATA_DIR}/sold"
ACTIVE_FILE = f"{DATA_DIR}/active"
LIMITED_FILE = f"{DATA_DIR}/limited"


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

    try:
        response = rq.get("https://api.hypixel.net/v2/skyblock/auctions_ended", stream=True)
        response.raise_for_status()
        data = response.json()

        for auction in data["auctions"]:
            parse_item(items, auction)
    except rq.RequestException as e:
        print(f"Error fetching sold auctions: {e}")


def merge_auctions(items: dict) -> None:
    now = datetime.now().timestamp()

    def merge_source(source_file):
        try:
            with open(source_file, "rb") as file:
                source = pickle.load(file)
                for key, value in source.items():
                    existing = items.get(key, {})
                    timestamp = existing.get("timestamp", now)

                    if timestamp + 604_800 > now and key in items:
                        continue

                    items[key] = value
                    items[key]["timestamp"] = now
        except (FileNotFoundError, pickle.UnpicklingError) as e:
            print(f"Error merging data from {source_file}: {e}")

    merge_source(ACTIVE_FILE)
    merge_source(LIMITED_FILE)


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
    send_data(url=URL, data={"items": ah}, key=KEY)
