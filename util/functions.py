import json
import os
import pickle
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


def save_data(data: dict, name: str, log: bool) -> None:
    """
    Save data to a file.

    :param: data - Data to be saved.
    :param: name - Name of the file to save the data to.
    :param: log - Whether to log the data.
    :return: None
    """

    # Make sure all directories exist
    os.makedirs("data/pickle", exist_ok=True)
    os.makedirs("data/json", exist_ok=True)

    # Save the data
    with open(f"data/pickle/{name}", "wb") as file:
        pickle.dump(data, file)

    # Log the data
    if log:
        with open(f"data/json/{name}.json", "w") as file:
            json.dump(data, file, indent=4)


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
