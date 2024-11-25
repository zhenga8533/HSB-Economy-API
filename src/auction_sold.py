import os
from dotenv import load_dotenv
from util.functions import *
from util.items import *
from util.logger import setup_logger


def get_sold_auction(logger: logging.Logger) -> None:
    """
    Get the latest sold auction data and store it in the provided 'items' dictionary.

    :param logger: The logger to use.
    :return: None
    """

    # Fetch last parsed auction
    auction = get_data("auction.json", logger) or {}

    # Fetch the Auction data
    data = fetch_data("https://api.hypixel.net/v2/skyblock/auctions_ended", "auction_sold", logger, True)

    auctions = data["auctions"]
    for item in auctions:
        update_lbin(auction=auction, item=item)

    # Save and return the auction data
    save_data(auction, "auction.json", logger)
    return auction


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    INCREMENT = int(os.getenv("INCREMENT"))
    KEY = os.getenv("KEY")
    LOG = os.getenv("LOG") == "True"
    URL = os.getenv("AUCTION_URL")
    logger = setup_logger("auction", "logs/auction_sold.log") if LOG else None

    # Fetch data
    auction = get_sold_auction(logger=logger)
    print(auction)

    # Save and send data
    # send_data(url=URL, data={"items": ah}, key=KEY)
