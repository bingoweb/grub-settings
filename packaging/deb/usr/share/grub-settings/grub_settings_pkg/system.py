import os
import shutil
import subprocess
import logging
from .utils import logger

class GrubPaths:
    """Determine GRUB paths and update commands based on distribution."""

    def __init__(self):
        self.distro_info = self._parse_os_release()
        self.grub_file = "/etc/default/grub"
        self.grub_cfg = self._detect_grub_cfg()
        self.efi_path = self._detect_efi_path()
        self.update_cmd = self._detect_update_command()

        logger.info(f"Distro: {self.distro_info.get('ID', 'unknown')} ({self.distro_info.get('PRETTY_NAME', 'Unknown Linux')})")
        logger.info(f"GRUB Config: {self.grub_cfg}")
        logger.info(f"EFI Path: {self.efi_path}")
        logger.info(f"Update Command: {self.update_cmd}")

    def _parse_os_release(self):
        """Standard /etc/os-release parsing"""
        info = {}
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        if '=' in line:
                            k, v = line.strip().split('=', 1)
                            info[k] = v.strip('"')
        except Exception as e:
            logger.warning(f"OS release read failed: {e}")
        return info

    def _detect_grub_cfg(self):
        candidates = [
            "/boot/grub/grub.cfg",      # Debian, Ubuntu, Arch, Linux Mint
            "/boot/grub2/grub.cfg",     # Fedora, RHEL, SUSE
            "/boot/efi/EFI/fedora/grub.cfg",
            "/boot/efi/EFI/redhat/grub.cfg",
        ]

        for path in candidates:
            if os.path.exists(path):
                return path
        return "/boot/grub/grub.cfg"

    def _detect_efi_path(self):
        candidates = ["/boot/efi", "/efi", "/boot"]
        for path in candidates:
            if os.path.exists(os.path.join(path, "EFI")):
                return path
        return "/boot/efi"

    def _detect_update_command(self):
        distro_id = self.distro_info.get('ID', '').lower()
        distro_like = self.distro_info.get('ID_LIKE', '').lower()

        if shutil.which("update-grub"):
            return "update-grub"

        if 'fedora' in distro_id or 'rhel' in distro_id or 'suse' in distro_id or \
           'fedora' in distro_like or 'rhel' in distro_like or 'suse' in distro_like:
            if shutil.which("grub2-mkconfig"):
                return f"grub2-mkconfig -o {self.grub_cfg}"

        if shutil.which("grub-mkconfig"):
            return f"grub-mkconfig -o {self.grub_cfg}"

        if shutil.which("grub2-mkconfig"):
            return f"grub2-mkconfig -o {self.grub_cfg}"

        return "update-grub"

# Global instance for easy access
PATHS = GrubPaths()
GRUB_FILE = PATHS.grub_file
GRUB_CFG_FILE = PATHS.grub_cfg
