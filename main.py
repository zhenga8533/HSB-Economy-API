import requests as rq
from dotenv import load_dotenv
import os
from auction import get_auction
from bazaar import get_bazaar


def send_data(url, data, key):
    """
    Send data to the API via POST request.

    :param url: URL to POST to
    :param data: Data to be sent
    :param key: API key needed to make a POST request
    :return: API response
    """
    response = rq.post(url, json=data, params={'key': key})
    return response.json()


if __name__ == "__main__":
    load_dotenv()
    KEY = os.getenv('KEY')

    send_data(os.getenv('AUCTION_URL'), {'items': get_auction(0)}, KEY)
    send_data(os.getenv('BAZAAR_URL'), {'items': get_bazaar()}, KEY)
