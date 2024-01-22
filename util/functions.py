import base64
import gzip
import io
from nbtlib import Compound


def decode_nbt(auction: dict) -> dict:
    """
    Decode => Decompress => Warp in io.BytesIO to parse the Base64-encoded data

    :param auction: Auction data containing the item information
    :return: Parsed NBT data as a Compound object
    """

    encoded_data = auction["item_bytes"]
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
