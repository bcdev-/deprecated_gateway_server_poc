import multiprocessing
import importlib
import time
from common.settings import currencies

import logging
logger = logging.getLogger(__name__)

deposit_handlers = []
plugins = [importlib.import_module("plugins.%s.deposit_handler" % p) for p in currencies.values()]
for plugin in plugins:
    if hasattr(plugin, 'DepositHandler'):
        deposit_handlers.append(plugin.DepositHandler())


class PluginManager(multiprocessing.Process):

    def _main_loop(self):
        for deposit_handler in deposit_handlers:
            deposit_handler.tick()

    def run(self):
        logger.info("Started")
        for deposit_handler in deposit_handlers:
            deposit_handler.start()
        while True:
            self._main_loop()
            time.sleep(1)
