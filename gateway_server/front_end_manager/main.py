import multiprocessing
from .web_server import start_webserver

import logging
logger = logging.getLogger(__name__)


class FrontEndManager(multiprocessing.Process):
    def run(self):
        logger.info("Started")
    start_webserver()
