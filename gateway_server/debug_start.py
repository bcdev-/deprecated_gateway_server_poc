#!/usr/bin/env python3
import sys
import time
import logging
from front_end_manager.main import FrontEndManager
from plugin_manager.main import PluginManager
from common.settings import set_loglevel

set_loglevel(logging.DEBUG)

if sys.version_info < (3,0):
    print("This program has to be run with Python 3 interpreter.")
    print("Try: python3 %s" % sys.argv[0])
    sys.exit(1)

if __name__ == "__main__":
    front_end_manager = FrontEndManager()
    front_end_manager.start()
    plugin_manager = PluginManager()
    plugin_manager.start()

    def terminate_all():
        front_end_manager.terminate()
        plugin_manager.terminate()
        exit(0)

    while True:
        if not front_end_manager.is_alive():
            terminate_all()
        if not plugin_manager.is_alive():
            terminate_all()
        time.sleep(0.03)

