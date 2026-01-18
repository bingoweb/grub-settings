import logging
import os
import shutil
import subprocess
from typing import Dict, List

from .utils import logger


class GrubPaths:
    """Determine GRUB paths and update commands based on Linux distribution.

    This class automatically detects the Linux distribution and determines
    the appropriate GRUB configuration paths and update commands.

    Attributes:
        distro_info (Dict[str, str]): Distribution information from /etc/os-release
        grub_file (str): Path to GRUB configuration file (/etc/default/grub)
        grub_cfg (str): Path to generated GRUB config (grub.cfg)
        efi_path (str): Path to EFI partition mount point
        update_cmd (str): Command to update GRUB configuration
    """

    def __init__(self) -> None:
        """Initialize GrubPaths by detecting distribution and paths."""
        self.distro_info: Dict[str, str] = self._parse_os_release()
        self.grub_file: str = "/etc/default/grub"
        self.grub_cfg: str = self._detect_grub_cfg()
        self.efi_path: str = self._detect_efi_path()
        self.update_cmd: str = self._detect_update_command()

        logger.info(
            f"Distro: {self.distro_info.get('ID', 'unknown')} ({self.distro_info.get('PRETTY_NAME', 'Unknown Linux')})"
        )
        logger.info(f"GRUB Config: {self.grub_cfg}")
        logger.info(f"EFI Path: {self.efi_path}")
        logger.info(f"Update Command: {self.update_cmd}")

    def _parse_os_release(self) -> Dict[str, str]:
        """Parse /etc/os-release file for distribution information.

        Returns:
            Dict[str, str]: Distribution information (ID, VERSION_ID, PRETTY_NAME, etc.)
        """
        info: Dict[str, str] = {}
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            info[k] = v.strip('"')
        except (OSError, IOError) as e:
            logger.warning(f"OS release file I/O error: {e}")
        except Exception as e:
            logger.warning(f"OS release parse error: {e}")
        return info

    def _detect_grub_cfg(self) -> str:
        """Detect GRUB configuration file path based on distribution.

        Returns:
            str: Path to grub.cfg file
        """
        candidates: List[str] = [
            "/boot/grub/grub.cfg",  # Debian, Ubuntu, Arch, Linux Mint
            "/boot/grub2/grub.cfg",  # Fedora, RHEL, SUSE
            "/boot/efi/EFI/fedora/grub.cfg",
            "/boot/efi/EFI/redhat/grub.cfg",
        ]

        for path in candidates:
            if os.path.exists(path):
                return path
        return "/boot/grub/grub.cfg"  # Default fallback

    def _detect_efi_path(self) -> str:
        """Detect EFI system partition mount point.

        Returns:
            str: Path to EFI partition (usually /boot/efi)
        """
        candidates: List[str] = ["/boot/efi", "/efi", "/boot"]
        for path in candidates:
            if os.path.exists(os.path.join(path, "EFI")):
                return path
        return "/boot/efi"  # Default fallback

    def _detect_update_command(self) -> str:
        """Detect appropriate GRUB update command for current distribution.

        Returns:
            str: GRUB update command (update-grub, grub-mkconfig, or grub2-mkconfig)
        """
        distro_id: str = self.distro_info.get("ID", "").lower()
        distro_like: str = self.distro_info.get("ID_LIKE", "").lower()

        # Debian/Ubuntu style
        if shutil.which("update-grub"):
            return "update-grub"

        # Fedora/RHEL/SUSE style
        if (
            "fedora" in distro_id
            or "rhel" in distro_id
            or "suse" in distro_id
            or "fedora" in distro_like
            or "rhel" in distro_like
            or "suse" in distro_like
        ):
            if shutil.which("grub2-mkconfig"):
                return f"grub2-mkconfig -o {self.grub_cfg}"

        # Arch Linux style
        if shutil.which("grub-mkconfig"):
            return f"grub-mkconfig -o {self.grub_cfg}"

        # Fallback to grub2-mkconfig
        if shutil.which("grub2-mkconfig"):
            return f"grub2-mkconfig -o {self.grub_cfg}"

        return "update-grub"  # Default fallback


# Global instance for easy access
PATHS = GrubPaths()
GRUB_FILE = PATHS.grub_file
GRUB_CFG_FILE = PATHS.grub_cfg
