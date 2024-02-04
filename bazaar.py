import requests as rq

BAZAAR_URL = 'https://api.hypixel.net/v2/skyblock/bazaar'


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
    products = data['products']
    for product in products:
        item = products[product]
        quick_status = item['quick_status']

        items[product] = [quick_status['sellPrice'], quick_status['buyPrice']]
    # print('Bazaar Process Complete!')
