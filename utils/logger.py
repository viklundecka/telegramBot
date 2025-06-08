import logging
from config.settings import LOG_LEVEL, LOG_FILE


def setup_logger():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.getLogger('aiogram').setLevel(logging.WARNING)