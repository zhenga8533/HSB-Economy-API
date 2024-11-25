import base64
import gzip
import io
from nbtlib import Compound
from util.functions import *


def decode_nbt(auction: dict) -> dict:
    """
    Decode => Decompress => Warp in io.BytesIO to parse the Base64-encoded data

    :param: auction - Auction data containing the item information
    :return: Parsed NBT data as a Compound object
    """

    encoded_data = auction["item_bytes"]
    decoded_data = base64.b64decode(encoded_data)
    decompressed_data = gzip.decompress(decoded_data)
    return Compound.parse(io.BytesIO(decompressed_data))
