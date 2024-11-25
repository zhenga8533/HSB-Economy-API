import json
import logging
import os
import requests as rq
from dotenv import load_dotenv


def fetch_data(url: str, logger: logging.Logger) -> dict:
    """
    Fetch data from the API via GET request.

    :param: url - URL to GET from
    :param: logger - Logger to log the response
    :return: API response
    """
    load_dotenv()
    RETRIES = int(os.getenv("RETRIES"))
    TIMEOUT = int(os.getenv("TIMEOUT"))

    for attempt in range(RETRIES):
        try:
            logger.info(f"Fetching data from {url}...")
            response = rq.get(url, timeout=TIMEOUT)

            if response.status_code != 200:
                if logger:
                    logger.error(f"Failed to fetch data. Status code: {response.status_code}")
                continue
            elif logger:
                logger.info(f"Fetched data from {url}. Status code: {response.status_code}")

            # Parse the data and cache it if needed
            data = response.json()
            if logger:
                cache_data(data, "bazaar", logger)
            return data
        except rq.exceptions.Timeout:
            if logger:
                logger.error(f"Attempt {attempt + 1} timed out while fetching data from {url}.")
        except rq.exceptions.RequestException as e:
            if logger:
                logger.error(f"Attempt {attempt + 1} failed to fetch data from {url}.")

    logger.error(f"Failed to fetch data from {url} after {RETRIES} attempts.")
    exit(1)


def cache_data(data: dict, name: str, logger: logging.Logger) -> None:
    """
    Cache data to a file.

    :param: data - Data to be cached.
    :param: name - Name of the file to cache the data to.
    :param: logger - Logger to log the data.
    :return: None
    """

    # Make sure all directories exist
    os.makedirs("cache", exist_ok=True)

    # Cache the data
    logger.info(f"Caching data to cache/{name}.json...")
    with open(f"cache/{name}.json", "w") as file:
        json.dump(data, file, indent=4)
    logger.info(f"Data cached to cache/{name}.json.")


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
    if logger:
        logger.info(f"Data sent to {url}. Status code: {response.status_code}")

    return response.json()
