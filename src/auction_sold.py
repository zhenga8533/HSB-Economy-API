import os
from dotenv import load_dotenv
from util.functions import *
from util.logger import setup_logger


def get_sold_auction(logger: logging.Logger) -> None:
    """
    Get the latest sold auction data and store it in the provided 'items' dictionary.

    :param logger: The logger to use.
    :return: None
    """

    # Fetch the Auction data
    if logger:
        logger.info("Fetching Auction data...")
    data = fetch_data("https://api.hypixel.net/v2/skyblock/auctions_ended", logger)

    # Loop through the products and store the data
    auctions = data["auctions"]
    auction = {}

    for item in auctions:
        continue

    return auction


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    INCREMENT = int(os.getenv("INCREMENT"))
    KEY = os.getenv("KEY")
    LOG = os.getenv("LOG") == "True"
    URL = os.getenv("AUCTION_URL")
    logger = setup_logger("auction", "logs/auction.log") if LOG else None

    # Fetch data
    auction = get_sold_auction(logger=logger)

    # Save and send data
    # send_data(url=URL, data={"items": ah}, key=KEY)
