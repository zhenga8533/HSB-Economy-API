import requests as rq
import os
from dotenv import load_dotenv
from util.functions import *


def get_bazaar(items: dict) -> None:
    """
    Gets the latest Bazaar data and stores it in the provided 'items' dictionary.

    :param: items - A dictionary containing information about items, where keys are item IDs.
    :return: None
    """

    response = rq.get("https://api.hypixel.net/v2/skyblock/bazaar")

    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return

    data = response.json()
    products = data["products"]
    for product in products:
        item = products[product]
        quick_status = item["quick_status"]

        items[product] = [quick_status["sellPrice"], quick_status["buyPrice"]]


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    KEY = os.getenv("KEY")
    LOG = os.getenv("LOG") == "True"
    URL = os.getenv("BAZAAR_URL")

    # Fetch and send data
    bazaar = {}
    get_bazaar(bazaar)
    save_data(bazaar, "bazaar", LOG)
    send_data(url=URL, data={"items": bazaar}, key=KEY)
