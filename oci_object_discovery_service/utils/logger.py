import logging
import sys

# Create a logger
logger = logging.getLogger("ods")
logger.setLevel(logging.DEBUG)  # Change to INFO/ERROR in production

# Avoid adding handlers multiple times if logger is imported in many places
if not logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Add handler
    logger.addHandler(console_handler)

    # Optional: prevent duplicate logs if root logger is also used
    logger.propagate = False
