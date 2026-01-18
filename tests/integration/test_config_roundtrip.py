"""Integration tests for config roundtrip operations."""
import pytest
from pathlib import Path
from grub_settings_pkg.config import GrubConfig


@pytest.mark.integration
class TestConfigRoundtrip:
    """Integration tests for reading, modifying, and writing GRUB configs."""

    def test_roundtrip_ubuntu_config(self, ubuntu_grub_config, tmp_path, mocker):
        """Test full roundtrip with Ubuntu config."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(ubuntu_grub_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        # Load config
        gc = GrubConfig()
        original_timeout = gc.get("GRUB_TIMEOUT")

        # Modify
        gc.set("GRUB_TIMEOUT", "10")
        gc.set("GRUB_CMDLINE_LINUX", "quiet splash nouveau.modeset=0")

        # Generate
        new_config = gc.generate_config()

        # Parse generated config
        gc2 = GrubConfig()
        gc2.raw_content = new_config
        gc2.config.clear()
        for line in gc2.raw_content.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                gc2.config[key.strip()] = value.strip().strip('"').strip("'")

        # Verify changes persisted
        assert gc2.get("GRUB_TIMEOUT") == "10"
        assert gc2.get("GRUB_CMDLINE_LINUX") == "quiet splash nouveau.modeset=0"

        # Verify other values preserved
        assert gc2.get("GRUB_DEFAULT") == gc.get("GRUB_DEFAULT")

    def test_roundtrip_fedora_config(self, fedora_grub_config, tmp_path, mocker):
        """Test full roundtrip with Fedora config."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(fedora_grub_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        # Load config
        gc = GrubConfig()

        # Modify
        gc.set("GRUB_TIMEOUT", "3")
        gc.set("GRUB_DISABLE_RECOVERY", "false")

        # Generate
        new_config = gc.generate_config()

        # Verify structure preserved
        assert "GRUB_TIMEOUT=3" in new_config
        assert 'GRUB_DISABLE_RECOVERY=false' in new_config or 'GRUB_DISABLE_RECOVERY="false"' in new_config

    def test_roundtrip_preserves_comments(self, commented_options_config, tmp_path, mocker):
        """Test that comments are preserved during roundtrip."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(commented_options_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        # Load config
        gc = GrubConfig()

        # Uncomment one option
        gc.set("GRUB_DISABLE_OS_PROBER", "false")

        # Generate
        new_config = gc.generate_config()

        # Verify comment preservation
        assert "# This option is commented out" in new_config
        assert "GRUB_DISABLE_OS_PROBER=false" in new_config

    def test_roundtrip_special_characters(self, special_chars_config, tmp_path, mocker):
        """Test roundtrip with special characters."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(special_chars_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        # Load config
        gc = GrubConfig()
        original_cmdline = gc.get("GRUB_CMDLINE_LINUX")

        # Modify with more special chars
        gc.set("GRUB_CMDLINE_LINUX", "quiet splash $vt_handoff init=/bin/bash")

        # Generate
        new_config = gc.generate_config()

        # Verify special chars preserved and quoted
        assert 'GRUB_CMDLINE_LINUX="quiet splash $vt_handoff init=/bin/bash"' in new_config

    def test_add_new_option_to_existing_config(self, minimal_grub_config, tmp_path, mocker):
        """Test adding new options to existing config."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(minimal_grub_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        # Load minimal config
        gc = GrubConfig()

        # Add multiple new options
        gc.set("GRUB_CMDLINE_LINUX", "quiet splash")
        gc.set("GRUB_DISABLE_OS_PROBER", "false")
        gc.set("GRUB_GFXMODE", "1920x1080")

        # Generate
        new_config = gc.generate_config()

        # Verify all new options added
        assert 'GRUB_CMDLINE_LINUX="quiet splash"' in new_config
        assert "GRUB_DISABLE_OS_PROBER=false" in new_config
        assert "GRUB_GFXMODE=1920x1080" in new_config

        # Verify original options preserved
        assert "GRUB_DEFAULT=0" in new_config
        assert "GRUB_TIMEOUT=5" in new_config

    def test_remove_option_from_config(self, ubuntu_grub_config, tmp_path, mocker):
        """Test removing options from config."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(ubuntu_grub_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        # Load config
        gc = GrubConfig()

        # Remove an option
        gc.remove("GRUB_TIMEOUT_STYLE")

        # Generate
        new_config = gc.generate_config()

        # Verify option removed from active config
        assert "GRUB_TIMEOUT_STYLE=" not in [
            line for line in new_config.splitlines()
            if line.strip() and not line.strip().startswith('#')
        ]

    def test_multiple_modifications_persist(self, ubuntu_grub_config, tmp_path, mocker):
        """Test that multiple sequential modifications all persist."""
        grub_file = tmp_path / "grub"
        grub_file.write_text(ubuntu_grub_config)
        mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

        # Load config
        gc = GrubConfig()

        # Multiple modifications
        gc.set("GRUB_TIMEOUT", "15")
        gc.set("GRUB_DEFAULT", "saved")
        gc.set("GRUB_CMDLINE_LINUX_DEFAULT", "quiet splash nomodeset")
        gc.remove("GRUB_TIMEOUT_STYLE")
        gc.set("GRUB_DISABLE_OS_PROBER", "false")

        # Generate
        new_config = gc.generate_config()

        # Verify all modifications
        assert "GRUB_TIMEOUT=15" in new_config
        assert "GRUB_DEFAULT=saved" in new_config
        assert 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash nomodeset"' in new_config
        assert "GRUB_DISABLE_OS_PROBER=false" in new_config
