import sys

from .app import GrubSettingsApp
from .config import config_manager
from .utils import logger, setup_i18n


def global_exception_handler(exctype, value, traceback_obj):
    import os
    import traceback
    from datetime import datetime

    # Use XDG Cache location
    crash_dir = os.path.expanduser("~/.cache/grub-settings")
    os.makedirs(crash_dir, exist_ok=True)
    crash_file = os.path.join(crash_dir, "crash.log")

    with open(crash_file, "w") as f:
        f.write(f"Crash Time: {datetime.now()}\n")
        traceback.print_exception(exctype, value, traceback_obj, file=f)
    print(f"CRITICAL ERROR (Uncaught): {value}")
    try:
        logging.critical(f"Uncaught exception: {value}", exc_info=(exctype, value, traceback_obj))
    except:
        pass


def main():
    sys.excepthook = global_exception_handler

    # Setup i18n before app starts
    setup_i18n(config_manager)

    try:
        app = GrubSettingsApp()
        app.run(sys.argv)
    except Exception as e:
        global_exception_handler(type(e), e, e.__traceback__)


if __name__ == "__main__":
    main()
