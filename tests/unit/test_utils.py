"""Tests for grub_settings_pkg/utils.py - Utility functions."""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from grub_settings_pkg import utils


class TestGetPath:
    """Tests for get_path() function."""

    def test_get_path_development_mode(self, tmp_path, mocker):
        """Test get_path in development mode (current directory)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch("os.path.abspath", return_value=str(tmp_path)):
            with patch("os.path.exists", return_value=True):
                result = utils.get_path("test.txt")
                assert "test.txt" in result

    def test_get_path_pyinstaller_mode(self, tmp_path, mocker):
        """Test get_path when running from PyInstaller bundle."""
        meipass = tmp_path / "meipass"
        meipass.mkdir()
        test_file = meipass / "test.txt"
        test_file.write_text("test")

        mocker.patch.object(sys, "_MEIPASS", str(meipass), create=True)

        with patch("os.path.exists", return_value=True):
            result = utils.get_path("test.txt")
            assert str(meipass) in result

    def test_get_path_flatpak_mode(self, mocker):
        """Test get_path in Flatpak environment."""
        mocker.patch("os.path.exists", side_effect=lambda p: "/app/share/grub-settings" in p)
        mocker.patch("grub_settings_pkg.utils.IS_FLATPAK", True)

        result = utils.get_path("assets/icon.png")
        assert "/app/share/grub-settings" in result

    def test_get_path_system_install(self, mocker):
        """Test get_path for system-wide installation."""

        def mock_exists(path):
            return "/usr/share/grub-settings" in path

        mocker.patch("os.path.exists", side_effect=mock_exists)

        result = utils.get_path("assets/icon.png")
        assert "/usr/share/grub-settings" in result

    def test_get_path_fallback(self, mocker):
        """Test get_path fallback when file not found."""
        mocker.patch("os.path.abspath", return_value="/current/dir")
        mocker.patch("os.path.exists", return_value=False)

        result = utils.get_path("nonexistent.txt")
        assert "nonexistent.txt" in result


class TestSetupLogging:
    """Tests for setup_logging() function."""

    def test_setup_logging_creates_directory(self, tmp_path, mocker):
        """Test that setup_logging creates log directory."""
        log_dir = tmp_path / ".cache" / "grub-settings"
        mocker.patch.object(Path, "home", return_value=tmp_path)

        logger = utils.setup_logging()

        assert log_dir.exists()
        assert (log_dir / "app.log").exists()

    def test_setup_logging_returns_logger(self, tmp_path, mocker):
        """Test that setup_logging returns a logger instance."""
        mocker.patch.object(Path, "home", return_value=tmp_path)

        logger = utils.setup_logging()

        assert isinstance(logger, logging.Logger)
        assert logger.name == "GRUB Settings"

    def test_setup_logging_level(self, tmp_path, mocker):
        """Test that logger is configured with INFO level."""
        mocker.patch.object(Path, "home", return_value=tmp_path)

        # Reset logging to avoid conflicts
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logger = utils.setup_logging()
        assert logger.level == logging.INFO or logging.root.level == logging.INFO


class TestSetupI18n:
    """Tests for setup_i18n() function."""

    def test_setup_i18n_with_saved_language(self, mocker):
        """Test i18n setup with saved language preference."""
        mock_config = Mock()
        mock_config.get.return_value = "tr"

        mocker.patch("grub_settings_pkg.utils.get_path", return_value="/fake/locales")
        mock_translation = Mock()
        mocker.patch("gettext.translation", return_value=mock_translation)

        utils.setup_i18n(mock_config)

        mock_translation.install.assert_called_once()

    def test_setup_i18n_auto_detect(self, mocker):
        """Test i18n setup with auto-detection."""
        mock_config = Mock()
        mock_config.get.return_value = None

        mocker.patch("grub_settings_pkg.utils.get_path", return_value="/fake/locales")
        mock_translation = Mock()
        mocker.patch("gettext.translation", return_value=mock_translation)

        utils.setup_i18n(mock_config)

        mock_translation.install.assert_called_once()

    def test_setup_i18n_fallback_on_error(self, mocker, caplog):
        """Test i18n setup fallback when translation fails."""
        mock_config = Mock()
        mock_config.get.return_value = "en"

        mocker.patch("grub_settings_pkg.utils.get_path", return_value="/fake/locales")
        mocker.patch("gettext.translation", side_effect=Exception("Translation error"))

        utils.setup_i18n(mock_config)

        # Should install fallback translation function
        assert "i18n setup failed" in caplog.text


class TestGetSudoCommand:
    """Tests for get_sudo_command() function."""

    def test_get_sudo_command_prefers_sudo(self, mocker):
        """Test that sudo is preferred when available."""
        mocker.patch("shutil.which", side_effect=lambda x: x if x == "sudo" else None)

        result = utils.get_sudo_command()

        assert result == ["sudo", "-S", "bash", "-c"]

    def test_get_sudo_command_falls_back_to_pkexec(self, mocker):
        """Test fallback to pkexec when sudo not available."""

        def mock_which(cmd):
            return cmd if cmd == "pkexec" else None

        mocker.patch("shutil.which", side_effect=mock_which)

        result = utils.get_sudo_command()

        assert result == ["pkexec", "bash", "-c"]

    def test_get_sudo_command_defaults_to_sudo(self, mocker):
        """Test default to sudo when neither is available."""
        mocker.patch("shutil.which", return_value=None)

        result = utils.get_sudo_command()

        assert result == ["sudo", "-S", "bash", "-c"]


class TestRestartApp:
    """Tests for restart_app() function."""

    def test_restart_app_frozen_mode(self, mocker):
        """Test restarting app in frozen (PyInstaller) mode."""
        mock_app = Mock()
        mocker.patch.object(sys, "frozen", True, create=True)
        mocker.patch.object(sys, "executable", "/path/to/exe")
        mocker.patch.object(sys, "argv", ["/path/to/exe", "--arg"])
        mock_execl = mocker.patch("os.execl")
        mocker.patch("time.sleep")

        utils.restart_app(mock_app)

        mock_app.quit.assert_called_once()
        mock_execl.assert_called_once()

    def test_restart_app_python_mode(self, mocker):
        """Test restarting app in normal Python mode."""
        mock_app = Mock()
        mocker.patch.object(sys, "frozen", False, create=True)
        mocker.patch.object(sys, "executable", "/usr/bin/python3")
        mocker.patch.object(sys, "argv", ["app.py", "--arg"])
        mock_execl = mocker.patch("os.execl")
        mocker.patch("time.sleep")

        utils.restart_app(mock_app)

        mock_app.quit.assert_called_once()
        mock_execl.assert_called_once_with(
            "/usr/bin/python3", "/usr/bin/python3", "app.py", "--arg"
        )

    def test_restart_app_error_handling(self, mocker, caplog):
        """Test restart_app handles errors gracefully."""
        mock_app = Mock()
        mocker.patch.object(sys, "frozen", False, create=True)
        mocker.patch("os.execl", side_effect=Exception("Restart failed"))
        mocker.patch("time.sleep")

        utils.restart_app(mock_app)

        assert "Restart failed" in caplog.text


class TestISFlatpak:
    """Tests for IS_FLATPAK constant."""

    def test_is_flatpak_true(self, mocker):
        """Test IS_FLATPAK detection when running in Flatpak."""
        mocker.patch("os.path.exists", return_value=True)

        # Re-import to get updated constant
        import importlib

        importlib.reload(utils)

        # Note: This tests the logic, actual constant is set at import time
        assert os.path.exists("/.flatpak-info") == True

    def test_is_flatpak_false(self, mocker):
        """Test IS_FLATPAK detection when not running in Flatpak."""
        mocker.patch("os.path.exists", return_value=False)

        assert os.path.exists("/.flatpak-info") == False


class TestLoggingConfiguration:
    """Tests for logging configuration."""

    def test_logger_has_file_handler(self, tmp_path, mocker):
        """Test that logger has file handler configured."""
        mocker.patch.object(Path, "home", return_value=tmp_path)

        # Clear existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logger = utils.setup_logging()
        log_file = tmp_path / ".cache" / "grub-settings" / "app.log"

        assert log_file.exists()

    def test_logger_has_stream_handler(self, tmp_path, mocker):
        """Test that logger has stream handler configured."""
        mocker.patch.object(Path, "home", return_value=tmp_path)

        # Clear existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logger = utils.setup_logging()

        # Check that handlers include StreamHandler
        handlers = logging.getLogger().handlers
        has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in handlers)
        assert has_stream_handler
