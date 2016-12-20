import multiprocessing
import importlib
import time
from common.settings import currencies

import logging
logger = logging.getLogger(__name__)

class PluginManager(multiprocessing.Process):

    def _main_loop(self):
        for deposit_handler in self.deposit_handlers:
            if not isinstance(deposit_handler, multiprocessing.Process):
                deposit_handler.tick()

    def run(self):
        logger.info("Started")

        self.deposit_handlers = []
        plugins = [importlib.import_module("plugins.%s.deposit_handler" % p) for p in currencies.values()]
        for plugin in plugins:
            if hasattr(plugin, 'DepositHandler'):
                self.deposit_handlers.append(plugin.DepositHandler())

        for deposit_handler in self.deposit_handlers:
            deposit_handler.start()
        while True:
            self._main_loop()
            time.sleep(1)
