import requests as rq
import base64
import gzip
import io
from nbtlib import Compound


def send_data(url: str, data: dict, key: str) -> dict:
    """
    Send data to the API via POST request.

    :param: url - URL to POST to
    :param: data - Data to be sent
    :param: key - API key needed to make a POST request
    :return: API response
    """

    response = rq.post(url, json=data, params={'key': key})
    return response.json()


def decode_nbt(auction: dict) -> dict:
    """
    Decode => Decompress => Warp in io.BytesIO to parse the Base64-encoded data

    :param: auction - Auction data containing the item information
    :return: Parsed NBT data as a Compound object
    """

    encoded_data = auction['item_bytes']
    decoded_data = base64.b64decode(encoded_data)
    decompressed_data = gzip.decompress(decoded_data)
    return Compound.parse(io.BytesIO(decompressed_data))


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


def is_within_percentage(number1: float, number2: float, percentage: float) -> bool:
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
