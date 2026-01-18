"""Input validation and sanitization for GRUB Settings.

This module provides validation and sanitization functions to ensure
safe and correct GRUB configuration modifications.
"""

import os
import re
from pathlib import Path
from typing import Any, Optional, Tuple

from .utils import logger

# Allowed GRUB configuration keys (whitelist approach)
ALLOWED_GRUB_KEYS = {
    # Boot settings
    "GRUB_DEFAULT",
    "GRUB_SAVEDEFAULT",
    "GRUB_TIMEOUT",
    "GRUB_TIMEOUT_STYLE",
    "GRUB_HIDDEN_TIMEOUT",
    "GRUB_HIDDEN_TIMEOUT_QUIET",
    # Display settings
    "GRUB_GFXMODE",
    "GRUB_GFXPAYLOAD_LINUX",
    "GRUB_TERMINAL",
    "GRUB_TERMINAL_INPUT",
    "GRUB_TERMINAL_OUTPUT",
    "GRUB_BACKGROUND",
    "GRUB_THEME",
    # Kernel parameters
    "GRUB_CMDLINE_LINUX",
    "GRUB_CMDLINE_LINUX_DEFAULT",
    "GRUB_CMDLINE_XEN",
    "GRUB_CMDLINE_XEN_DEFAULT",
    # OS detection
    "GRUB_DISABLE_OS_PROBER",
    "GRUB_OS_PROBER_SKIP_LIST",
    "GRUB_DISABLE_SUBMENU",
    # Recovery mode
    "GRUB_DISABLE_RECOVERY",
    # Distribution
    "GRUB_DISTRIBUTOR",
    # Boot loader
    "GRUB_ENABLE_BLSCFG",
    "GRUB_ENABLE_CRYPTODISK",
    # Serial console
    "GRUB_SERIAL_COMMAND",
    # Badram
    "GRUB_BADRAM",
    # Init tune
    "GRUB_INIT_TUNE",
    # Recordfail
    "GRUB_RECORDFAIL_TIMEOUT",
    # Linux UUID
    "GRUB_DISABLE_LINUX_UUID",
    "GRUB_DISABLE_LINUX_PARTUUID",
}


# Dangerous characters that should be escaped or removed
DANGEROUS_CHARS = {
    "\x00",  # Null byte
    "\r",  # Carriage return (can cause injection)
    "\n",  # Newline (can cause injection)
}

# Shell command injection patterns
SHELL_INJECTION_PATTERNS = [
    r";",  # Command separator
    r"\|",  # Pipe
    r"&&",  # AND operator
    r"\|\|",  # OR operator
    r"`",  # Command substitution (allowed in some contexts)
    r"\$\(",  # Command substitution
    r">",  # Redirection
    r"<",  # Redirection
]


def validate_grub_key(key: Any) -> Tuple[bool, Optional[str]]:
    """Validate GRUB configuration key.

    Args:
        key: GRUB configuration key to validate (can be any type for validation)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not key:
        return False, "Key cannot be empty"

    if not isinstance(key, str):
        return False, "Key must be a string"

    # Check if key is in whitelist
    if key not in ALLOWED_GRUB_KEYS:
        logger.warning(f"Unknown GRUB key: {key}")
        # Don't reject, just warn - allows for future GRUB options

    # Check for dangerous characters
    if any(c in key for c in DANGEROUS_CHARS):
        return False, "Key contains dangerous characters"

    # Key should only contain uppercase letters, numbers, and underscores
    if not re.match(r"^[A-Z_][A-Z0-9_]*$", key):
        return False, "Key must match pattern: ^[A-Z_][A-Z0-9_]*$"

    return True, None


def sanitize_grub_value(value: Any, allow_shell: bool = False) -> str:
    """Sanitize GRUB configuration value.

    Args:
        value: Value to sanitize (will be converted to string)
        allow_shell: Whether to allow shell constructs (backticks, $, etc.)

    Returns:
        str: Sanitized value
    """
    if value is None:
        return ""

    value_str = str(value)

    # Remove dangerous null bytes and control characters
    for char in DANGEROUS_CHARS:
        value_str = value_str.replace(char, "")

    # Check for shell injection if not allowed
    if not allow_shell:
        for pattern in SHELL_INJECTION_PATTERNS:
            if re.search(pattern, value_str):
                logger.warning(f"Potentially dangerous pattern '{pattern}' found in value")
                # Don't remove, but log - some patterns are legitimate in GRUB

    return value_str


def validate_timeout(timeout: Any) -> Tuple[bool, Optional[str]]:
    """Validate GRUB timeout value.

    Args:
        timeout: Timeout value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        timeout_int = int(timeout)
    except (ValueError, TypeError):
        return False, "Timeout must be an integer"

    if timeout_int < -1:
        return False, "Timeout must be -1 (wait indefinitely) or >= 0"

    if timeout_int > 999:
        return False, "Timeout must be <= 999 seconds"

    return True, None


def validate_gfxmode(gfxmode: str) -> Tuple[bool, Optional[str]]:
    """Validate GRUB_GFXMODE value.

    Args:
        gfxmode: Graphics mode string (e.g., "1920x1080", "auto")

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not gfxmode:
        return False, "Graphics mode cannot be empty"

    # Allow special values
    if gfxmode.lower() in ["auto", "keep", "text"]:
        return True, None

    # Validate resolution format (e.g., 1920x1080, 1024x768x24)
    pattern = r"^\d{3,5}x\d{3,5}(x\d{1,2})?$"
    if not re.match(pattern, gfxmode):
        return False, "Invalid graphics mode format (expected: WIDTHxHEIGHT or WIDTHxHEIGHTxDEPTH)"

    # Check reasonable resolution limits
    parts = gfxmode.split("x")
    width = int(parts[0])
    height = int(parts[1])

    if width < 640 or width > 7680:
        return False, "Width must be between 640 and 7680"

    if height < 480 or height > 4320:
        return False, "Height must be between 480 and 4320"

    return True, None


def validate_file_path(path: str, must_exist: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate file path for security.

    Args:
        path: File path to validate
        must_exist: Whether file must exist

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path cannot be empty"

    try:
        # Convert to Path object for validation
        path_obj = Path(path)

        # Check for directory traversal attempts
        resolved = path_obj.resolve()

        # Ensure path is absolute after resolution
        if not resolved.is_absolute():
            return False, "Path must be absolute"

        # Check for common dangerous paths
        dangerous_parents = ["/etc/shadow", "/etc/passwd", "/root/.ssh"]
        for dangerous in dangerous_parents:
            if str(resolved).startswith(dangerous):
                return False, f"Access to {dangerous} is not allowed"

        # Check existence if required
        if must_exist and not resolved.exists():
            return False, f"Path does not exist: {path}"

        return True, None

    except (ValueError, OSError) as e:
        return False, f"Invalid path: {e}"


def validate_boolean(value: Any) -> Tuple[bool, Optional[str]]:
    """Validate boolean value for GRUB config.

    Args:
        value: Value to validate as boolean

    Returns:
        Tuple of (is_valid, error_message)
    """
    if isinstance(value, bool):
        return True, None

    if isinstance(value, str):
        if value.lower() in ["true", "false", "yes", "no", "1", "0"]:
            return True, None

    return False, "Boolean value must be 'true', 'false', 'yes', 'no', '1', or '0'"


def sanitize_cmdline(cmdline: str) -> Tuple[str, bool]:
    """Sanitize kernel command line parameters.

    Args:
        cmdline: Kernel command line string

    Returns:
        Tuple of (sanitized_cmdline, had_changes)
    """
    original = cmdline

    # Remove dangerous null bytes
    for char in DANGEROUS_CHARS:
        cmdline = cmdline.replace(char, "")

    # Split into individual parameters
    params = cmdline.split()

    # Validate each parameter
    safe_params = []
    for param in params:
        # Allow common kernel parameter patterns
        # name=value or just name
        # Allow $ for variables like $vt_handoff
        if re.match(r"^[a-zA-Z0-9_\-\.\$]+(?:=[a-zA-Z0-9_\-\.\:\/\,\+\*\$\{\}]+)?$", param):
            safe_params.append(param)
        else:
            logger.warning(f"Suspicious kernel parameter removed: {param}")

    sanitized = " ".join(safe_params)
    had_changes = sanitized != original

    return sanitized, had_changes
