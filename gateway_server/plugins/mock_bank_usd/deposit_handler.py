import logging
logger = logging.getLogger(__name__)


class DepositHandler:
    def start(self):
        logger.info("Starting")

    def tick(self):
        logger.debug("Tick")
