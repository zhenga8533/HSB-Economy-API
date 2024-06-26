import requests as rq
import os
from dotenv import load_dotenv
from util.functions import send_data

BAZAAR_URL = "https://api.hypixel.net/v2/skyblock/bazaar"


def get_bazaar(items: dict) -> None:
    """
    Fetches data from the specified BAZAAR_URL and updates the provided 'items' dictionary with bazaar information.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    response = rq.get(BAZAAR_URL)

    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return

    data = response.json()
    products = data["products"]
    for product in products:
        item = products[product]
        quick_status = item["quick_status"]

        items[product] = [quick_status["sellPrice"], quick_status["buyPrice"]]
    # print('Bazaar Process Complete!')


def send_items(items: dict) -> None:
    """
    Sends the provided 'items' data using an API call.

    :param: items - A dictionary containing lbin information about items.
    :return: None
    """

    load_dotenv()
    KEY = os.getenv("KEY")
    send_data(os.getenv("AUCTION_URL"), {"items": items}, KEY)


if __name__ == "__main__":
    load_dotenv()
    KEY = os.getenv("KEY")
    bazaar = {}
    get_bazaar(bazaar)

    # Send to API
    send_data(os.getenv("BAZAAR_URL"), {"items": bazaar}, KEY)
