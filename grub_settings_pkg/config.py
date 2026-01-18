import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from . import validation
from .system import GRUB_FILE
from .utils import logger


class ConfigManager:
    """Manages application settings (user preferences).

    This class handles loading, saving, and managing user configuration
    stored in ~/.config/grub-settings/settings.json

    Attributes:
        config_dir (Path): Directory containing configuration files
        config_file (Path): Path to the settings.json file
        config (Dict[str, Any]): In-memory configuration dictionary
    """

    def __init__(self) -> None:
        """Initialize ConfigManager with default paths and load existing config."""
        self.config_dir: Path = Path.home() / ".config" / "grub-settings"
        self.config_file: Path = self.config_dir / "settings.json"
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file.

        Returns:
            Dict[str, Any]: Configuration dictionary or empty dict on error
        """
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                if not isinstance(loaded_config, dict):
                    logger.warning("Invalid config format, expected dict")
                    return {}
                return loaded_config
        except json.JSONDecodeError as e:
            logger.warning(f"Config JSON decode failed: {e}")
            return {}
        except (OSError, IOError) as e:
            logger.warning(f"Config file I/O error: {e}")
            return {}

    def save_config(self) -> bool:
        """Save current configuration to JSON file.

        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except (OSError, IOError) as e:
            logger.error(f"Config save I/O error: {e}")
            return False
        except TypeError as e:
            logger.error(f"Config contains non-serializable data: {e}")
            return False

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key to retrieve
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set configuration value and save to disk.

        Args:
            key: Configuration key to set
            value: Value to store (must be JSON-serializable)

        Returns:
            bool: True if save successful, False otherwise
        """
        self.config[key] = value
        return self.save_config()


class GrubConfig:
    """Reads and writes the /etc/default/grub file.

    This class manages GRUB bootloader configuration by parsing,
    modifying, and regenerating the /etc/default/grub file while
    preserving comments and formatting.

    Attributes:
        config (Dict[str, str]): Parsed GRUB configuration key-value pairs
        raw_content (str): Original file content for preserving structure
    """

    def __init__(self) -> None:
        """Initialize GrubConfig and load current GRUB configuration."""
        self.config: Dict[str, str] = {}
        self.raw_content: str = ""
        self.load()

    def load(self) -> bool:
        """Read and parse GRUB settings from /etc/default/grub.

        Returns:
            bool: True if successfully loaded, False on error

        Raises:
            No exceptions are raised; errors are logged instead
        """
        try:
            if not os.path.exists(GRUB_FILE):
                logger.error(f"GRUB file not found: {GRUB_FILE}")
                return False

            with open(GRUB_FILE, "r", encoding="utf-8") as f:
                self.raw_content = f.read()

            self.config.clear()
            for line in self.raw_content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    self.config[key] = value

            logger.info(f"GRUB config loaded: {len(self.config)} settings")
            return True
        except PermissionError:
            logger.error("No permission to read GRUB file")
            return False
        except (OSError, IOError) as e:
            logger.error(f"Failed to read GRUB file (I/O error): {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to read GRUB file (unexpected error): {e}")
            return False

    def get(self, key: str, default: str = "") -> str:
        """Get GRUB configuration value by key.

        Args:
            key: Configuration key (e.g., 'GRUB_TIMEOUT')
            default: Default value if key not found

        Returns:
            str: Configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any, skip_validation: bool = False) -> bool:
        """Set GRUB configuration value with validation.

        Args:
            key: Configuration key (e.g., 'GRUB_TIMEOUT')
            value: Value to set (will be converted to string)
            skip_validation: Skip validation (use with caution)

        Returns:
            bool: True if value was set, False if validation failed

        Raises:
            ValueError: If validation fails and skip_validation is False
        """
        if not skip_validation:
            # Validate key
            is_valid, error = validation.validate_grub_key(key)
            if not is_valid:
                error_msg = f"Invalid GRUB key '{key}': {error}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Apply specific validation based on key type
            if key == "GRUB_TIMEOUT":
                is_valid, error = validation.validate_timeout(value)
                if not is_valid:
                    error_msg = f"Invalid timeout value: {error}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            elif key == "GRUB_GFXMODE":
                is_valid, error = validation.validate_gfxmode(str(value))
                if not is_valid:
                    error_msg = f"Invalid graphics mode: {error}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            elif key == "GRUB_BACKGROUND":
                if value:  # Only validate if not empty
                    is_valid, error = validation.validate_file_path(str(value), must_exist=False)
                    if not is_valid:
                        logger.warning(f"Background path validation: {error}")

            elif key in [
                "GRUB_DISABLE_OS_PROBER",
                "GRUB_DISABLE_RECOVERY",
                "GRUB_DISABLE_SUBMENU",
                "GRUB_SAVEDEFAULT",
            ]:
                is_valid, error = validation.validate_boolean(value)
                if not is_valid:
                    logger.warning(f"Boolean validation: {error}")

            elif key in ["GRUB_CMDLINE_LINUX", "GRUB_CMDLINE_LINUX_DEFAULT"]:
                # Sanitize kernel command line
                sanitized, had_changes = validation.sanitize_cmdline(str(value))
                if had_changes:
                    logger.warning(f"Kernel cmdline was sanitized: {value} -> {sanitized}")
                    value = sanitized

        # Sanitize value
        sanitized_value = validation.sanitize_grub_value(
            value, allow_shell=(key == "GRUB_DISTRIBUTOR")  # Allow shell constructs for distributor
        )

        self.config[key] = sanitized_value
        logger.debug(f"Setting changed: {key} = {sanitized_value}")
        return True

    def remove(self, key: str) -> None:
        """Remove configuration key from GRUB settings.

        Args:
            key: Configuration key to remove
        """
        if key in self.config:
            del self.config[key]
            logger.debug(f"Setting removed: {key}")

    def generate_config(self) -> str:
        """Regenerate config content preserving comments and structure.

        This method rebuilds the GRUB configuration file content while:
        - Preserving all comment lines
        - Maintaining original file structure
        - Uncommenting keys that are being set
        - Adding quotes to values with spaces or special characters
        - Appending new keys at the end

        Returns:
            str: Complete GRUB configuration file content
        """
        lines = []
        processed_keys: set = set()

        for line in self.raw_content.splitlines():
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                # Handle commented out keys that we might want to uncomment
                if stripped.startswith("#") and "=" in stripped:
                    comment_content = stripped[1:].strip()
                    if "=" in comment_content:
                        key = comment_content.split("=", 1)[0].strip()
                        if key in self.config and key not in processed_keys:
                            value = self.config[key]
                            # Add quotes if needed
                            if " " in str(value) or any(c in str(value) for c in ["$", "`", '"']):
                                lines.append(f'{key}="{value}"')
                            else:
                                lines.append(f"{key}={value}")
                            processed_keys.add(key)
                            continue
                lines.append(line)
                continue

            if "=" in stripped:
                key = stripped.split("=", 1)[0]
                if key in self.config:
                    value = self.config[key]
                    if " " in str(value) or any(c in str(value) for c in ["$", "`", '"']):
                        lines.append(f'{key}="{value}"')
                    else:
                        lines.append(f"{key}={value}")
                    processed_keys.add(key)
                else:
                    lines.append(line)
            else:
                lines.append(line)

        # Add new keys
        for key, value in self.config.items():
            if key not in processed_keys:
                if " " in str(value) or any(c in str(value) for c in ["$", "`", '"']):
                    lines.append(f'{key}="{value}"')
                else:
                    lines.append(f"{key}={value}")

        return "\n".join(lines)


# Global instance
config_manager = ConfigManager()
