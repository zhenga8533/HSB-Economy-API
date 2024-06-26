import requests as rq


def check_replace(current: dict, item_bin: float, now: int) -> bool:
    """
    Check if the current item should be replaced with the new item.

    :param: current - The current item data.
    :param: item_bin - The new item's bin price.
    :param: now - The current timestamp.
    :return: True if the item should be replaced, False otherwise.
    """

    return (
        current is None
        or item_bin < current.get("lbin")
        or current.get("timestamp", 0) + 604_800 < now
        or within_percent(item_bin, current.get("lbin"), 5)
    )


def send_data(url: str, data: dict, key: str) -> dict:
    """
    Send data to the API via POST request.

    :param: url - URL to POST to
    :param: data - Data to be sent
    :param: key - API key needed to make a POST request
    :return: API response
    """

    response = rq.post(url, json=data, params={"key": key})
    return response.json()


def average_objects(og: dict, avg: dict, count: int) -> None:
    """
    Recursively computes the average of values in nested dictionaries.

    :param: og - The original dictionary to be averaged.
    :param: avg - The dictionary containing values to be averaged with the original.
    :param: count - The count of elements used for averaging.
    :return: None
    """
    for key, value in avg.items():
        if key not in og:
            og[key] = value
            continue

        if isinstance(og[key], dict):
            average_objects(og[key], avg[key], count)
        else:  # Bias average on current hour
            og[key] = round(og[key] + (avg[key] - og[key]) / count)


def within_percent(number1: float, number2: float, percentage: float) -> bool:
    """
    Check if number1 is within a certain percentage of number2.

    :param: number1 - The first number to compare.
    :param: number2 - The second number to compare against.
    :param: percentage - The percentage within which to check.
    :return: True if number1 is within the specified percentage of number2, False otherwise.
    """
    threshold = (percentage / 100) * max(abs(number1), abs(number2))
    difference = abs(number1 - number2)
    return difference <= threshold
