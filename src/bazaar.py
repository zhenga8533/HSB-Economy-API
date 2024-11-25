import logging
import requests as rq
import os
from dotenv import load_dotenv
from util.functions import *
from util.logger import setup_logger


def get_bazaar(logger: logging.Logger) -> dict:
    """
    Gets the latest Bazaar data and stores it in the provided 'items' dictionary.

    :param logger: The logger to use.
    :return: A dictionary containing the latest Bazaar data.
    """

    if logger:
        logger.info("Fetching Bazaar data...")
    bazaar = {}
    response = rq.get("https://api.hypixel.net/v2/skyblock/bazaar")
    if logger:
        logger.info(f"Fetched Bazaar data. Status code: {response.status_code}")

    if response.status_code != 200:
        if logger:
            logger.error(f"Failed to fetch Bazaar data. Status code: {response.status_code}")
        exit(1)

    data = response.json()
    products = data["products"]
    for product in products:
        item = products[product]
        quick_status = item["quick_status"]

        if logger:
            logger.info(
                f"Item: {product}, Buy Price: {quick_status['buyPrice']}, Sell Price: {quick_status['sellPrice']}"
            )

        bazaar[product] = [quick_status["sellPrice"], quick_status["buyPrice"]]

    return bazaar


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    KEY = os.getenv("KEY")
    LOG = os.getenv("LOG") == "True"
    URL = os.getenv("BAZAAR_URL")
    logger = setup_logger("bazaar", "logs/bazaar.log") if LOG else None

    # Fetch and send data
    bazaar = get_bazaar(logger=logger)
    save_data(data=bazaar, name="bazaar", logger=logger)
    send_data(url=URL, data={"items": bazaar}, key=KEY, logger=logger)
