import os
import sys
import logging
import shutil
import gettext
from pathlib import Path
from .constants import APP_NAME

# Check if running in Flatpak
IS_FLATPAK = os.path.exists("/.flatpak-info")

def get_path(relative_path):
    """Get absolute path to resource, handling development and installed modes."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)
    if os.path.exists(path):
        return path

    if IS_FLATPAK:
        flatpak_path = os.path.join("/app/share/grub-settings", relative_path)
        if os.path.exists(flatpak_path):
            return flatpak_path

    # Fallback for system install (Debian)
    system_path = os.path.join("/usr/share/grub-settings", relative_path)
    if os.path.exists(system_path):
        return system_path

    return path

def setup_logging():
    """Configure logging to file and stream."""
    log_dir = Path.home() / ".cache" / "grub-settings"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(APP_NAME)

logger = setup_logging()

def setup_i18n(config_manager):
    """Setup internationalization."""
    try:
        locales_dir = get_path("locales")
        saved_lang = config_manager.get("language", None)

        if saved_lang:
            # Load user preference
            lang_code = "tr" if "tr" in saved_lang else "en"
            t = gettext.translation('grub-settings', localedir=locales_dir, languages=[lang_code])
        else:
            # Auto-detect
            t = gettext.translation('grub-settings', localedir=locales_dir, fallback=True)

        t.install() # Installs _()
    except Exception as e:
        logger.warning(f"i18n setup failed: {e}")
        import builtins
        builtins._ = lambda x: x

def get_sudo_command():
    """Return the sudo command appropriate for the system."""
    if shutil.which("sudo"):
        return ["sudo", "-S", "bash", "-c"]
    elif shutil.which("pkexec"):
        return ["pkexec", "bash", "-c"]
    else:
        return ["sudo", "-S", "bash", "-c"]

def restart_app(app):
    """Restart the application."""
    logger.info("Restarting application...")
    try:
        app.quit()
        import time
        time.sleep(0.5)

        if getattr(sys, 'frozen', False):
            os.execl(sys.executable, sys.executable, *sys.argv[1:])
        else:
            python = sys.executable
            os.execl(python, python, *sys.argv)
    except Exception as e:
        logger.error(f"Restart failed: {e}")
