import os
from dotenv import load_dotenv
from util.functions import send_data
from active_auction import get_active_auction
from bazaar import get_bazaar


if __name__ == '__main__':
    load_dotenv()
    KEY = os.getenv('KEY')

    # Get data to send
    auction = {}
    get_active_auction(auction, 0)
    bazaar = {}
    get_bazaar(bazaar)

    # Send to API
    print(auction)
    send_data(os.getenv('BAZAAR_URL'), {'items': bazaar}, KEY)
