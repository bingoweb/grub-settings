"""Tests for grub_settings_pkg/config.py - Configuration management."""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch
from grub_settings_pkg.config import ConfigManager, GrubConfig


class TestConfigManager:
    """Tests for ConfigManager class (user preferences)."""

    def test_init_creates_config_structure(self):
        """Test that ConfigManager initializes with proper paths."""
        cm = ConfigManager()
        assert cm.config_dir == Path.home() / ".config" / "grub-settings"
        assert cm.config_file == cm.config_dir / "settings.json"
        assert isinstance(cm.config, dict)

    def test_load_config_nonexistent_file(self, tmp_path, mocker):
        """Test loading config when file doesn't exist."""
        mocker.patch.object(Path, 'home', return_value=tmp_path)
        cm = ConfigManager()
        assert cm.config == {}

    def test_load_config_valid_json(self, tmp_path, mocker):
        """Test loading valid JSON config."""
        config_dir = tmp_path / ".config" / "grub-settings"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "settings.json"
        test_data = {"theme": "dark", "language": "en"}
        config_file.write_text(json.dumps(test_data))

        mocker.patch.object(Path, 'home', return_value=tmp_path)
        cm = ConfigManager()
        assert cm.config == test_data

    def test_load_config_invalid_json(self, tmp_path, mocker, caplog):
        """Test loading invalid JSON config returns empty dict."""
        config_dir = tmp_path / ".config" / "grub-settings"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "settings.json"
        config_file.write_text("{invalid json")

        mocker.patch.object(Path, 'home', return_value=tmp_path)
        cm = ConfigManager()
        assert cm.config == {}
        assert "Config JSON decode failed" in caplog.text

    def test_save_config_creates_directory(self, tmp_path, mocker):
        """Test that save_config creates directory if it doesn't exist."""
        mocker.patch.object(Path, 'home', return_value=tmp_path)
        cm = ConfigManager()
        cm.config = {"test": "value"}
        cm.save_config()

        assert cm.config_dir.exists()
        assert cm.config_file.exists()
        saved_data = json.loads(cm.config_file.read_text())
        assert saved_data == {"test": "value"}

    def test_save_config_overwrites_existing(self, tmp_path, mocker):
        """Test that save_config overwrites existing file."""
        config_dir = tmp_path / ".config" / "grub-settings"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "settings.json"
        config_file.write_text('{"old": "data"}')

        mocker.patch.object(Path, 'home', return_value=tmp_path)
        cm = ConfigManager()
        cm.config = {"new": "data"}
        cm.save_config()

        saved_data = json.loads(config_file.read_text())
        assert saved_data == {"new": "data"}

    def test_get_existing_key(self):
        """Test getting existing config key."""
        cm = ConfigManager()
        cm.config = {"theme": "dark"}
        assert cm.get("theme") == "dark"

    def test_get_nonexistent_key_default(self):
        """Test getting nonexistent key returns default."""
        cm = ConfigManager()
        assert cm.get("nonexistent") is None
        assert cm.get("nonexistent", "default") == "default"

    def test_set_saves_config(self, tmp_path, mocker):
        """Test that set() saves config to disk."""
        mocker.patch.object(Path, 'home', return_value=tmp_path)
        cm = ConfigManager()
        cm.set("theme", "light")

        assert cm.config["theme"] == "light"
        assert cm.config_file.exists()
        saved_data = json.loads(cm.config_file.read_text())
        assert saved_data["theme"] == "light"


class TestGrubConfig:
    """Tests for GrubConfig class (GRUB configuration)."""

    def test_init_loads_config(self, mocker):
        """Test that GrubConfig loads on initialization."""
        mock_load = mocker.patch.object(GrubConfig, 'load', return_value=True)
        gc = GrubConfig()
        assert mock_load.called

    def test_load_missing_file(self, tmp_path, mocker, caplog):
        """Test loading when GRUB file doesn't exist."""
        grub_file = tmp_path / "nonexistent"
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        result = gc.load()

        assert result is False
        assert "GRUB file not found" in caplog.text

    def test_load_permission_error(self, tmp_path, mocker, caplog):
        """Test loading with permission error."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_DEFAULT=0")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        with patch('builtins.open', side_effect=PermissionError):
            gc = GrubConfig()
            result = gc.load()

        assert result is False
        assert "No permission to read GRUB file" in caplog.text

    def test_parse_simple_values(self, tmp_path, mocker):
        """Test parsing simple key=value pairs."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_DEFAULT=0\nGRUB_TIMEOUT=5\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("GRUB_DEFAULT") == "0"
        assert gc.get("GRUB_TIMEOUT") == "5"

    def test_parse_quoted_values_double_quotes(self, tmp_path, mocker):
        """Test parsing values with double quotes."""
        grub_file = tmp_path / "grub"
        grub_file.write_text('GRUB_CMDLINE_LINUX="quiet splash"\n')
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("GRUB_CMDLINE_LINUX") == "quiet splash"

    def test_parse_quoted_values_single_quotes(self, tmp_path, mocker):
        """Test parsing values with single quotes."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_TIMEOUT_STYLE='menu'\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("GRUB_TIMEOUT_STYLE") == "menu"

    def test_parse_ignores_comments(self, tmp_path, mocker):
        """Test that comment lines are ignored during parsing."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("# This is a comment\nGRUB_DEFAULT=0\n#GRUB_TIMEOUT=10\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("GRUB_DEFAULT") == "0"
        assert gc.get("GRUB_TIMEOUT") == ""  # Commented out, not parsed

    def test_parse_empty_lines(self, tmp_path, mocker):
        """Test that empty lines are handled correctly."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("\n\nGRUB_DEFAULT=0\n\n\nGRUB_TIMEOUT=5\n\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert len(gc.config) == 2

    def test_parse_backtick_values(self, tmp_path, mocker):
        """Test parsing values with backticks (command substitution)."""
        grub_file = tmp_path / "grub"
        grub_file.write_text('GRUB_DISTRIBUTOR=`lsb_release -i -s 2> /dev/null || echo Debian`\n')
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        # The backticks should be preserved in the value
        assert "lsb_release" in gc.get("GRUB_DISTRIBUTOR")

    def test_parse_special_characters(self, tmp_path, mocker):
        """Test parsing values with special characters like $."""
        grub_file = tmp_path / "grub"
        grub_file.write_text('GRUB_CMDLINE_LINUX="quiet $vt_handoff"\n')
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("GRUB_CMDLINE_LINUX") == "quiet $vt_handoff"

    def test_get_existing_key(self, tmp_path, mocker):
        """Test getting existing GRUB config key."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_DEFAULT=0\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("GRUB_DEFAULT") == "0"

    def test_get_nonexistent_key_default(self, tmp_path, mocker):
        """Test getting nonexistent key returns default."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_DEFAULT=0\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("NONEXISTENT") == ""
        assert gc.get("NONEXISTENT", "default") == "default"

    def test_set_new_value(self, tmp_path, mocker):
        """Test setting a new GRUB config value."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.set("GRUB_TIMEOUT", "10")

        assert gc.config["GRUB_TIMEOUT"] == "10"

    def test_set_updates_existing_value(self, tmp_path, mocker):
        """Test that set() updates existing values."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_TIMEOUT=5\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.set("GRUB_TIMEOUT", "10")

        assert gc.config["GRUB_TIMEOUT"] == "10"

    def test_remove_existing_key(self, tmp_path, mocker):
        """Test removing an existing key."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_TIMEOUT=5\nGRUB_DEFAULT=0\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.remove("GRUB_TIMEOUT")

        assert "GRUB_TIMEOUT" not in gc.config
        assert "GRUB_DEFAULT" in gc.config

    def test_remove_nonexistent_key(self, tmp_path, mocker):
        """Test removing a nonexistent key doesn't error."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_DEFAULT=0\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.remove("NONEXISTENT")  # Should not raise error

    def test_generate_config_preserves_comments(self, tmp_path, mocker):
        """Test that generate_config preserves comment lines."""
        grub_file = tmp_path / "grub"
        content = "# This is a comment\nGRUB_DEFAULT=0\n# Another comment\n"
        grub_file.write_text(content)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        generated = gc.generate_config()

        assert "# This is a comment" in generated
        assert "# Another comment" in generated

    def test_generate_config_updates_existing_values(self, tmp_path, mocker):
        """Test that generate_config updates existing values."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_TIMEOUT=5\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.set("GRUB_TIMEOUT", "10")
        generated = gc.generate_config()

        assert "GRUB_TIMEOUT=10" in generated
        assert "GRUB_TIMEOUT=5" not in generated

    def test_generate_config_adds_new_keys(self, tmp_path, mocker):
        """Test that generate_config adds new keys at the end."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("GRUB_DEFAULT=0\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.set("GRUB_TIMEOUT", "10")
        generated = gc.generate_config()

        assert "GRUB_TIMEOUT=10" in generated
        assert "GRUB_DEFAULT=0" in generated

    def test_generate_config_quotes_values_with_spaces(self, tmp_path, mocker):
        """Test that values with spaces are quoted."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.set("GRUB_CMDLINE_LINUX", "quiet splash")
        generated = gc.generate_config()

        assert 'GRUB_CMDLINE_LINUX="quiet splash"' in generated

    def test_generate_config_quotes_values_with_special_chars(self, tmp_path, mocker):
        """Test that values with special chars ($, `, \") are quoted."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.set("GRUB_CMDLINE", "quiet $var")
        generated = gc.generate_config()

        assert 'GRUB_CMDLINE="quiet $var"' in generated

    def test_generate_config_uncomments_when_setting_value(self, tmp_path, mocker):
        """Test that commented options are uncommented when set."""
        grub_file = tmp_path / "grub"
        grub_file.write_text("#GRUB_DISABLE_OS_PROBER=false\n")
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        gc.set("GRUB_DISABLE_OS_PROBER", "false")
        generated = gc.generate_config()

        assert "GRUB_DISABLE_OS_PROBER=false" in generated
        assert "#GRUB_DISABLE_OS_PROBER=false" not in generated

    def test_generate_config_preserves_empty_lines(self, tmp_path, mocker):
        """Test that empty lines are preserved in structure."""
        grub_file = tmp_path / "grub"
        content = "GRUB_DEFAULT=0\n\nGRUB_TIMEOUT=5\n"
        grub_file.write_text(content)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        generated = gc.generate_config()
        lines = generated.split('\n')

        # Should have empty line preserved
        assert '' in lines

    def test_roundtrip_config(self, tmp_path, mocker):
        """Test parsing and regenerating config produces equivalent result."""
        grub_file = tmp_path / "grub"
        content = "# Comment\nGRUB_DEFAULT=0\nGRUB_TIMEOUT=5\n"
        grub_file.write_text(content)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        generated = gc.generate_config()

        # Parse the generated config
        gc2 = GrubConfig()
        gc2.raw_content = generated
        gc2.config.clear()
        for line in gc2.raw_content.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                gc2.config[key.strip()] = value.strip().strip('"').strip("'")

        assert gc.config == gc2.config

    def test_load_ubuntu_fixture(self, ubuntu_grub_config, tmp_path, mocker):
        """Test loading Ubuntu default GRUB config."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(ubuntu_grub_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("GRUB_DEFAULT") == "0"
        assert gc.get("GRUB_TIMEOUT") == "0"
        assert gc.get("GRUB_TIMEOUT_STYLE") == "hidden"
        assert gc.get("GRUB_CMDLINE_LINUX_DEFAULT") == "quiet splash"

    def test_load_fedora_fixture(self, fedora_grub_config, tmp_path, mocker):
        """Test loading Fedora default GRUB config."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(fedora_grub_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        gc = GrubConfig()
        assert gc.get("GRUB_TIMEOUT") == "5"
        assert gc.get("GRUB_DEFAULT") == "saved"
        assert gc.get("GRUB_DISABLE_SUBMENU") == "true"
