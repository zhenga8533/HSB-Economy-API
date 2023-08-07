import requests as rq
from auction_api.auction import get_auction
from auction_api.bazaar import get_bazaar


def send_data(url, data):
    """
    Send data to the API via POST request.

    :param url: URL to POST to
    :param data: Data to be sent
    :return: API response
    """
    response = rq.post(url, json=data)
    return response.json()


if __name__ == "__main__":
    send_data('https://volcaronitee.pythonanywhere.com/auction', {'items': get_auction(0)})
    send_data('https://volcaronitee.pythonanywhere.com/bazaar', {'items': get_bazaar()})
