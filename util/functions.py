import base64
import gzip
import io
from nbtlib import Compound
from datetime import datetime


def decode_nbt(auction: dict) -> dict:
    """
    Decode => Decompress => Warp in io.BytesIO to parse the Base64-encoded data

    :param auction: Auction data containing the item information
    :return: Parsed NBT data as a Compound object
    """

    encoded_data = auction['item_bytes']
    decoded_data = base64.b64decode(encoded_data)
    decompressed_data = gzip.decompress(decoded_data)
    return Compound.parse(io.BytesIO(decompressed_data))


def average_objects(og: dict, avg: dict, count: int) -> None:
    """
    Recursively computes the average of values in nested dictionaries.

    :param og: The original dictionary to be averaged.
    :param avg: The dictionary containing values to be averaged with the original.
    :param count: The count of elements used for averaging.
    """
    for key, value in avg.items():
        if key not in og:
            og[key] = value
            continue

        if isinstance(og[key], dict):
            average_objects(og[key], avg[key], count)
        else:  # Bias average on current hour
            og[key] = round(og[key] + (avg[key] - og[key]) / count)


def update_kuudra_piece(items: dict, item_id: str, attribute: str, attribute_cost: float) -> bool:
    """
    Parses Kuudra item into specific piece data to add to API.

    :param items: Auction items object to be sent to API.
    :param item_id: Name of item.
    :param attribute: Name of attribute.
    :param attribute_cost: Total value of attribute.
    :return: True if piece is a Kuudra piece otherwise False.
    """
    KUUDRA_PIECES = {'FERVOR', 'AURORA', 'TERROR', 'CRIMSON', 'HOLLOW', 'MOLTEN'}
    item_ids = item_id.split('_')

    if item_ids[0] in KUUDRA_PIECES:
        armor_piece = items.setdefault(item_ids[1], {'attributes': {}})

        # set individual attribute price
        attributes = armor_piece['attributes']
        current_cost = attributes[attribute]['lbin'] if attribute in attributes else attribute_cost
        if attribute_cost <= current_cost:
            attributes[attribute] = {'lbin': attribute_cost, 'timestamp': datetime.now().timestamp()}
        elif is_within_percentage(current_cost, attribute_cost, 5):
            attributes[attribute]['timestamp'] = datetime.now().timestamp()

        return True
    return False


def is_within_percentage(number1: float, number2: float, percentage: float) -> bool:
    """
    Check if number1 is within a certain percentage of number2.

    :param number1: The first number to compare.
    :param number2: The second number to compare against.
    :param percentage: The percentage within which to check.
    :return: True if number1 is within the specified percentage of number2, False otherwise.
    """
    threshold = (percentage / 100) * max(abs(number1), abs(number2))
    difference = abs(number1 - number2)
    return difference <= threshold
