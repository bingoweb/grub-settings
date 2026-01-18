import os
import sys
import logging
import shutil
import gettext
from pathlib import Path
from typing import Any, List, Optional
from .constants import APP_NAME

# Check if running in Flatpak
IS_FLATPAK: bool = os.path.exists("/.flatpak-info")


def get_path(relative_path: str) -> str:
    """Get absolute path to resource, handling development and installed modes.

    This function checks multiple locations for resources in this order:
    1. PyInstaller bundle (sys._MEIPASS)
    2. Current working directory
    3. Flatpak installation (/app/share/grub-settings)
    4. System-wide installation (/usr/share/grub-settings)

    Args:
        relative_path: Relative path to resource (e.g., "assets/icon.png")

    Returns:
        str: Absolute path to the resource
    """
    try:
        base_path: str = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")

    path: str = os.path.join(base_path, relative_path)
    if os.path.exists(path):
        return path

    if IS_FLATPAK:
        flatpak_path: str = os.path.join("/app/share/grub-settings", relative_path)
        if os.path.exists(flatpak_path):
            return flatpak_path

    # Fallback for system install (Debian)
    system_path: str = os.path.join("/usr/share/grub-settings", relative_path)
    if os.path.exists(system_path):
        return system_path

    return path


def setup_logging() -> logging.Logger:
    """Configure logging to file and stream.

    Creates log directory at ~/.cache/grub-settings if it doesn't exist
    and sets up both file and console logging handlers.

    Returns:
        logging.Logger: Configured logger instance
    """
    log_dir: Path = Path.home() / ".cache" / "grub-settings"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file: Path = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(APP_NAME)


logger: logging.Logger = setup_logging()


def setup_i18n(config_manager: Any) -> None:
    """Setup internationalization with gettext.

    Args:
        config_manager: ConfigManager instance for retrieving language preference
    """
    try:
        locales_dir: str = get_path("locales")
        saved_lang: Optional[str] = config_manager.get("language", None)

        if saved_lang:
            # Load user preference
            lang_code: str = "tr" if "tr" in saved_lang else "en"
            t = gettext.translation('grub-settings', localedir=locales_dir, languages=[lang_code])
        else:
            # Auto-detect
            t = gettext.translation('grub-settings', localedir=locales_dir, fallback=True)

        t.install()  # Installs _() function globally
    except Exception as e:
        logger.warning(f"i18n setup failed: {e}")
        import builtins
        builtins._ = lambda x: x  # type: ignore


def get_sudo_command() -> List[str]:
    """Return the sudo command appropriate for the system.

    Checks for availability of sudo or pkexec and returns appropriate command.

    Returns:
        List[str]: Command list for privilege escalation
    """
    if shutil.which("sudo"):
        return ["sudo", "-S", "bash", "-c"]
    elif shutil.which("pkexec"):
        return ["pkexec", "bash", "-c"]
    else:
        return ["sudo", "-S", "bash", "-c"]  # Default fallback


def restart_app(app: Any) -> None:
    """Restart the application.

    Args:
        app: GTK Application instance to restart
    """
    logger.info("Restarting application...")
    try:
        app.quit()
        import time
        time.sleep(0.5)

        if getattr(sys, 'frozen', False):
            os.execl(sys.executable, sys.executable, *sys.argv[1:])
        else:
            python: str = sys.executable
            os.execl(python, python, *sys.argv)
    except Exception as e:
        logger.error(f"Restart failed: {e}")
