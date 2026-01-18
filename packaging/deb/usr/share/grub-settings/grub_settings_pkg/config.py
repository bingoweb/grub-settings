import json
import logging
import os
from pathlib import Path

from .system import GRUB_FILE
from .utils import logger


class ConfigManager:
    """Manages application settings (user preferences)."""

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "grub-settings"
        self.config_file = self.config_dir / "settings.json"
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
            return {}

    def save_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Config save failed: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()


class GrubConfig:
    """Reads and writes the /etc/default/grub file."""

    def __init__(self):
        self.config = {}
        self.raw_content = ""
        self.load()

    def load(self):
        """Read GRUB settings."""
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
        except Exception as e:
            logger.error(f"Failed to read GRUB file: {e}")
            return False

    def get(self, key, default=""):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = str(value)
        logger.debug(f"Setting changed: {key} = {value}")

    def remove(self, key):
        if key in self.config:
            del self.config[key]
            logger.debug(f"Setting removed: {key}")

    def generate_config(self):
        """Regenerate config content preserving comments and structure."""
        lines = []
        processed_keys = set()

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
