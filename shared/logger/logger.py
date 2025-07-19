# microservice/shared/logger/logger.py

import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(service_name: str, log_level: int = logging.INFO):
    """
    Creates and configures a logger for a specific service.

    Args:
        service_name (str): The name of the service using the logger.
        log_level (int): The logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        logging.Logger: A configured logger instance.
    """
    # Create the log directory if it doesn't exist
    log_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "log"
    )
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Define the log file path
    log_file = os.path.join(log_dir, f"{service_name}.log")

    # Create a logger
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)

    # Prevent log messages from being propagated to the root logger
    logger.propagate = False

    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Avoid adding duplicate handlers to the logger
    if not logger.handlers:
        # Create a rotating file handler
        # This will create a new file when the current one reaches 5MB, keeping up to 5 old log files.
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Create a console handler for printing logs to the console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
