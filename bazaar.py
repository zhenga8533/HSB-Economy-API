import requests as rq

BAZAAR_URL = 'https://api.hypixel.net/skyblock/bazaar'


def get_bazaar(items):
    """
    Fetch bazaar data and process items buy/sell data.
    """

    response = rq.get(BAZAAR_URL)

    if response.status_code != 200:
        print(f"Failed to get data. Status code: {response.status_code}")
        return {}

    data = response.json()
    products = data['products']
    for product in products:
        item = products[product]
        quick_status = item['quick_status']

        items[product] = [quick_status['sellPrice'], quick_status['buyPrice']]

    print('Bazaar Products Loaded!')
