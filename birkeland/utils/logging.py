import logging
from rich.logging import RichHandler

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    rich_handler = RichHandler(
        level=level,
        show_time=True,
        show_level=True,
        show_path=True,
        markup=True,
    )

    logger.addHandler(rich_handler)

    return logger
