import logging
import os


def setup_logger(name: str, path: str) -> logging.Logger:
    """
    Setup a logger with a file and stream handler.

    :param: name - Name of the logger
    :return: Logger object
    """

    # Create log directory if it doesn't exist
    log_dir = "/".join(path.split("/")[:-1])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # File handler
        file_handler = logging.FileHandler(path, mode="w")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
