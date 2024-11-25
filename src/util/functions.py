import json
import logging
import os
import pickle
import requests as rq


def save_data(data: dict, name: str, logger: logging.Logger) -> dict:
    """
    Save data to a file.

    :param: data - Data to be saved.
    :param: name - Name of the file to save the data to.
    :param: logger - Logger to log the data.
    :return: None
    """

    # Make sure all directories exist
    os.makedirs("data/pickle", exist_ok=True)
    os.makedirs("data/json", exist_ok=True)

    # Save the data
    with open(f"data/pickle/{name}", "wb") as file:
        pickle.dump(data, file)

    # Log the data
    if logger:
        logger.info(f"Data saved to data/pickle/{name}.json")
        with open(f"data/json/{name}.json", "w") as file:
            json.dump(data, file, indent=4)


def send_data(url: str, data: dict, key: str, logger: logging.Logger) -> dict:
    """
    Send data to the API via POST request.

    :param: url - URL to POST to
    :param: data - Data to be sent
    :param: key - API key needed to make a POST request
    :param: logger - Logger to log the response
    :return: API response
    """

    if logger:
        logger.info(f"Sending data to {url}...")
    response = rq.post(url, json=data, params={"key": key})
    return response.json()
