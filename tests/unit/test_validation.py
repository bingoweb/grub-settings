"""Tests for grub_settings_pkg/validation.py - Input validation and sanitization."""

import pytest

from grub_settings_pkg import validation


class TestValidateGrubKey:
    """Tests for validate_grub_key function."""

    def test_valid_grub_key(self):
        """Test validation of valid GRUB keys."""
        is_valid, error = validation.validate_grub_key("GRUB_TIMEOUT")
        assert is_valid is True
        assert error is None

    def test_valid_grub_default(self):
        """Test GRUB_DEFAULT key."""
        is_valid, error = validation.validate_grub_key("GRUB_DEFAULT")
        assert is_valid is True

    def test_empty_key(self):
        """Test empty key returns error."""
        is_valid, error = validation.validate_grub_key("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_key_with_lowercase(self):
        """Test key with lowercase letters."""
        is_valid, error = validation.validate_grub_key("grub_timeout")
        assert is_valid is False
        assert "pattern" in error

    def test_key_with_dangerous_chars(self):
        """Test key with null byte."""
        is_valid, error = validation.validate_grub_key("GRUB_TEST\x00")
        assert is_valid is False
        assert "dangerous" in error

    def test_key_with_special_chars(self):
        """Test key with special characters."""
        is_valid, error = validation.validate_grub_key("GRUB-TEST")
        assert is_valid is False


class TestValidateTimeout:
    """Tests for validate_timeout function."""

    def test_valid_timeout_zero(self):
        """Test timeout value of 0."""
        is_valid, error = validation.validate_timeout(0)
        assert is_valid is True

    def test_valid_timeout_positive(self):
        """Test positive timeout value."""
        is_valid, error = validation.validate_timeout(30)
        assert is_valid is True

    def test_valid_timeout_minus_one(self):
        """Test timeout value of -1 (infinite wait)."""
        is_valid, error = validation.validate_timeout(-1)
        assert is_valid is True

    def test_valid_timeout_string(self):
        """Test timeout as string number."""
        is_valid, error = validation.validate_timeout("10")
        assert is_valid is True

    def test_invalid_timeout_negative(self):
        """Test invalid negative timeout."""
        is_valid, error = validation.validate_timeout(-5)
        assert is_valid is False
        assert "must be -1" in error

    def test_invalid_timeout_too_large(self):
        """Test timeout value too large."""
        is_valid, error = validation.validate_timeout(1000)
        assert is_valid is False
        assert "999" in error

    def test_invalid_timeout_non_numeric(self):
        """Test non-numeric timeout value."""
        is_valid, error = validation.validate_timeout("invalid")
        assert is_valid is False
        assert "integer" in error


class TestValidateGfxmode:
    """Tests for validate_gfxmode function."""

    def test_valid_gfxmode_auto(self):
        """Test 'auto' gfxmode."""
        is_valid, error = validation.validate_gfxmode("auto")
        assert is_valid is True

    def test_valid_gfxmode_keep(self):
        """Test 'keep' gfxmode."""
        is_valid, error = validation.validate_gfxmode("keep")
        assert is_valid is True

    def test_valid_gfxmode_resolution(self):
        """Test resolution format."""
        is_valid, error = validation.validate_gfxmode("1920x1080")
        assert is_valid is True

    def test_valid_gfxmode_with_depth(self):
        """Test resolution with color depth."""
        is_valid, error = validation.validate_gfxmode("1024x768x24")
        assert is_valid is True

    def test_empty_gfxmode(self):
        """Test empty gfxmode."""
        is_valid, error = validation.validate_gfxmode("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_invalid_gfxmode_format(self):
        """Test invalid format."""
        is_valid, error = validation.validate_gfxmode("1920-1080")
        assert is_valid is False
        assert "Invalid graphics mode" in error

    def test_gfxmode_width_too_small(self):
        """Test width below minimum."""
        is_valid, error = validation.validate_gfxmode("320x240")
        assert is_valid is False
        assert "Width must be" in error

    def test_gfxmode_height_too_large(self):
        """Test height above maximum."""
        is_valid, error = validation.validate_gfxmode("1920x10000")
        assert is_valid is False
        assert "Height must be" in error


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_absolute_path(self):
        """Test valid absolute path."""
        is_valid, error = validation.validate_file_path("/boot/grub/background.jpg")
        assert is_valid is True

    def test_empty_path(self):
        """Test empty path."""
        is_valid, error = validation.validate_file_path("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_dangerous_path_shadow(self):
        """Test dangerous path /etc/shadow."""
        is_valid, error = validation.validate_file_path("/etc/shadow")
        assert is_valid is False
        assert "not allowed" in error

    def test_dangerous_path_ssh(self):
        """Test dangerous path /root/.ssh."""
        is_valid, error = validation.validate_file_path("/root/.ssh/id_rsa")
        assert is_valid is False
        assert "not allowed" in error


class TestValidateBoolean:
    """Tests for validate_boolean function."""

    def test_valid_boolean_true(self):
        """Test boolean True."""
        is_valid, error = validation.validate_boolean(True)
        assert is_valid is True

    def test_valid_boolean_false(self):
        """Test boolean False."""
        is_valid, error = validation.validate_boolean(False)
        assert is_valid is True

    def test_valid_string_true(self):
        """Test string 'true'."""
        is_valid, error = validation.validate_boolean("true")
        assert is_valid is True

    def test_valid_string_yes(self):
        """Test string 'yes'."""
        is_valid, error = validation.validate_boolean("yes")
        assert is_valid is True

    def test_valid_string_one(self):
        """Test string '1'."""
        is_valid, error = validation.validate_boolean("1")
        assert is_valid is True

    def test_invalid_boolean_string(self):
        """Test invalid boolean string."""
        is_valid, error = validation.validate_boolean("maybe")
        assert is_valid is False
        assert "Boolean value must be" in error


class TestSanitizeGrubValue:
    """Tests for sanitize_grub_value function."""

    def test_sanitize_simple_string(self):
        """Test simple string passes through."""
        result = validation.sanitize_grub_value("simple")
        assert result == "simple"

    def test_sanitize_null_value(self):
        """Test None value returns empty string."""
        result = validation.sanitize_grub_value(None)
        assert result == ""

    def test_sanitize_removes_null_bytes(self):
        """Test null bytes are removed."""
        result = validation.sanitize_grub_value("test\x00value")
        assert "\x00" not in result

    def test_sanitize_removes_newlines(self):
        """Test newlines are removed."""
        result = validation.sanitize_grub_value("test\nvalue")
        assert "\n" not in result

    def test_sanitize_integer(self):
        """Test integer conversion."""
        result = validation.sanitize_grub_value(123)
        assert result == "123"


class TestSanitizeCmdline:
    """Tests for sanitize_cmdline function."""

    def test_sanitize_valid_cmdline(self):
        """Test valid cmdline passes through."""
        sanitized, changed = validation.sanitize_cmdline("quiet splash")
        assert sanitized == "quiet splash"
        assert changed is False

    def test_sanitize_cmdline_with_equals(self):
        """Test cmdline with key=value format."""
        sanitized, changed = validation.sanitize_cmdline("root=/dev/sda1 ro")
        assert "root=/dev/sda1" in sanitized
        assert changed is False

    def test_sanitize_cmdline_complex(self):
        """Test complex cmdline parameters."""
        cmdline = "quiet splash acpi_osi=Linux nouveau.modeset=0"
        sanitized, changed = validation.sanitize_cmdline(cmdline)
        assert "quiet" in sanitized
        assert "splash" in sanitized
        assert changed is False

    def test_sanitize_removes_null_bytes(self):
        """Test null bytes are removed from cmdline."""
        cmdline = "quiet\x00 splash"
        sanitized, changed = validation.sanitize_cmdline(cmdline)
        assert "\x00" not in sanitized

    def test_sanitize_suspicious_params_removed(self):
        """Test suspicious parameters with semicolons are sanitized."""
        cmdline = "quiet splash ; echo bad"
        sanitized, changed = validation.sanitize_cmdline(cmdline)
        # Semicolon should be removed as it's invalid in kernel param names
        assert ";" not in sanitized
        # "echo" and "bad" are valid param names, so they'll stay
        assert changed is True


class TestAllowedGrubKeys:
    """Tests for ALLOWED_GRUB_KEYS constant."""

    def test_common_keys_allowed(self):
        """Test that common GRUB keys are in whitelist."""
        assert "GRUB_TIMEOUT" in validation.ALLOWED_GRUB_KEYS
        assert "GRUB_DEFAULT" in validation.ALLOWED_GRUB_KEYS
        assert "GRUB_CMDLINE_LINUX" in validation.ALLOWED_GRUB_KEYS
        assert "GRUB_GFXMODE" in validation.ALLOWED_GRUB_KEYS
        assert "GRUB_BACKGROUND" in validation.ALLOWED_GRUB_KEYS
        assert "GRUB_DISABLE_OS_PROBER" in validation.ALLOWED_GRUB_KEYS


class TestIntegrationValidation:
    """Integration tests for validation module."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        # Validate key
        is_valid, error = validation.validate_grub_key("GRUB_TIMEOUT")
        assert is_valid

        # Validate value
        is_valid, error = validation.validate_timeout(30)
        assert is_valid

        # Sanitize value
        sanitized = validation.sanitize_grub_value(30)
        assert sanitized == "30"
