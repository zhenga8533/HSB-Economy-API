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
        or within_percent(number1=item_bin, number2=current.get("lbin"), percentage=5)
    )


def clean_data(data: dict, low=0) -> None:
    """
    Cleans the provided 'items' dictionary by removing 'timestamp' entries and cleaning attribute dictionaries.

    :param: data - A dictionary containing information about items, where keys are item IDs.
    :param: low - Lowest cost item can be otherwise it is deleted.
    :return: None
    """

    keys = list(data.keys())

    for key in keys:
        item = data[key]

        # Remove timestamp
        if "timestamp" in item:
            del item["timestamp"]

        # Remove low items
        if data[key].get("lbin", 0) < low:
            del data[key]

        # Clean attributes
        if "attributes" in item:
            clean_data(data=item["attributes"])
        if "attribute_combos" in item:
            clean_data(data=item["attribute_combos"], low=25_000_000)


def increment_data(data: dict, increment: int) -> None:
    """
    Parses and updates the provided 'data' dictionary, removing entries with outdated timestamps,
    incrementing 'lbin' values, and applying similar updates to attribute and attribute_combos dictionaries.

    :param: data - A dictionary containing information about data, where keys are item IDs.
    :return: None
    """

    for key in data:
        item = data[key]

        # parse pricing
        if item.get("lbin", 0) != 0:
            item["lbin"] += increment

        # Parse attribute pricing
        if "attributes" in item:
            increment_data(data=item["attributes"], increment=increment)
        if "attribute_combos" in item:
            increment_data(data=item["attribute_combos"], increment=increment)


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
