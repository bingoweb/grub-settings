"""Tests for grub_settings_pkg/system.py - System detection and GRUB paths."""
import os
import pytest
from unittest.mock import Mock, patch, mock_open
from grub_settings_pkg.system import GrubPaths


class TestGrubPaths:
    """Tests for GrubPaths class."""

    def test_init_calls_detection_methods(self, mocker):
        """Test that initialization calls all detection methods."""
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")
        mocker.patch.object(GrubPaths, '_detect_update_command', return_value="update-grub")

        paths = GrubPaths()

        assert paths.distro_info == {}
        assert paths.grub_file == "/etc/default/grub"
        assert paths.grub_cfg == "/boot/grub/grub.cfg"
        assert paths.efi_path == "/boot/efi"
        assert paths.update_cmd == "update-grub"

    def test_parse_os_release_ubuntu(self, ubuntu_os_release, tmp_path, mocker):
        """Test parsing Ubuntu os-release file."""
        os_release_file = tmp_path / "os-release"
        os_release_file.write_text(ubuntu_os_release)

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=ubuntu_os_release)):
                paths = GrubPaths()
                info = paths._parse_os_release()

        assert info['ID'] == 'ubuntu'
        assert info['VERSION_ID'] == '22.04'
        assert info['ID_LIKE'] == 'debian'
        assert 'Ubuntu' in info['PRETTY_NAME']

    def test_parse_os_release_fedora(self, fedora_os_release, mocker):
        """Test parsing Fedora os-release file."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=fedora_os_release)):
                paths = GrubPaths()
                info = paths._parse_os_release()

        assert info['ID'] == 'fedora'
        assert info['VERSION_ID'] == '39'
        assert 'Fedora' in info['PRETTY_NAME']

    def test_parse_os_release_arch(self, arch_os_release, mocker):
        """Test parsing Arch Linux os-release file."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=arch_os_release)):
                paths = GrubPaths()
                info = paths._parse_os_release()

        assert info['ID'] == 'arch'
        assert info['PRETTY_NAME'] == 'Arch Linux'

    def test_parse_os_release_debian(self, debian_os_release, mocker):
        """Test parsing Debian os-release file."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=debian_os_release)):
                paths = GrubPaths()
                info = paths._parse_os_release()

        assert info['ID'] == 'debian'
        assert info['VERSION_ID'] == '12'
        assert info['VERSION_CODENAME'] == 'bookworm'

    def test_parse_os_release_rhel(self, rhel_os_release, mocker):
        """Test parsing RHEL os-release file."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=rhel_os_release)):
                paths = GrubPaths()
                info = paths._parse_os_release()

        assert info['ID'] == 'rhel'
        assert info['ID_LIKE'] == 'fedora'
        assert info['VERSION_ID'] == '9.3'

    def test_parse_os_release_missing_file(self, mocker):
        """Test parsing when os-release file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            paths = GrubPaths()
            info = paths._parse_os_release()

        assert info == {}

    def test_parse_os_release_permission_error(self, mocker, caplog):
        """Test parsing with permission error."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=PermissionError):
                paths = GrubPaths()
                info = paths._parse_os_release()

        assert info == {}
        assert "OS release file I/O error" in caplog.text

    def test_detect_grub_cfg_debian_style(self, mocker):
        """Test detecting Debian/Ubuntu style grub.cfg path."""
        def mock_exists(path):
            return path == "/boot/grub/grub.cfg"

        mocker.patch('os.path.exists', side_effect=mock_exists)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={})
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")
        mocker.patch.object(GrubPaths, '_detect_update_command', return_value="update-grub")

        paths = GrubPaths()
        cfg = paths._detect_grub_cfg()

        assert cfg == "/boot/grub/grub.cfg"

    def test_detect_grub_cfg_fedora_style(self, mocker):
        """Test detecting Fedora/RHEL style grub.cfg path."""
        def mock_exists(path):
            return path == "/boot/grub2/grub.cfg"

        mocker.patch('os.path.exists', side_effect=mock_exists)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={})
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")
        mocker.patch.object(GrubPaths, '_detect_update_command', return_value="grub2-mkconfig")

        paths = GrubPaths()
        cfg = paths._detect_grub_cfg()

        assert cfg == "/boot/grub2/grub.cfg"

    def test_detect_grub_cfg_fallback(self, mocker):
        """Test GRUB config detection fallback when no path exists."""
        mocker.patch('os.path.exists', return_value=False)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={})
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")
        mocker.patch.object(GrubPaths, '_detect_update_command', return_value="update-grub")

        paths = GrubPaths()
        cfg = paths._detect_grub_cfg()

        assert cfg == "/boot/grub/grub.cfg"  # Default fallback

    def test_detect_efi_path_boot_efi(self, mocker):
        """Test detecting EFI path at /boot/efi."""
        def mock_exists(path):
            return path == "/boot/efi/EFI"

        mocker.patch('os.path.exists', side_effect=mock_exists)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_update_command', return_value="update-grub")

        paths = GrubPaths()
        efi_path = paths._detect_efi_path()

        assert efi_path == "/boot/efi"

    def test_detect_efi_path_efi_root(self, mocker):
        """Test detecting EFI path at /efi."""
        def mock_exists(path):
            return path == "/efi/EFI"

        mocker.patch('os.path.exists', side_effect=mock_exists)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_update_command', return_value="update-grub")

        paths = GrubPaths()
        efi_path = paths._detect_efi_path()

        assert efi_path == "/efi"

    def test_detect_efi_path_fallback(self, mocker):
        """Test EFI path detection fallback."""
        mocker.patch('os.path.exists', return_value=False)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_update_command', return_value="update-grub")

        paths = GrubPaths()
        efi_path = paths._detect_efi_path()

        assert efi_path == "/boot/efi"  # Default fallback

    def test_detect_update_command_ubuntu_update_grub(self, mocker):
        """Test detecting update-grub command on Ubuntu/Debian."""
        mocker.patch('shutil.which', side_effect=lambda x: x if x == "update-grub" else None)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={'ID': 'ubuntu'})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")

        paths = GrubPaths()
        cmd = paths._detect_update_command()

        assert cmd == "update-grub"

    def test_detect_update_command_fedora_grub2_mkconfig(self, mocker):
        """Test detecting grub2-mkconfig on Fedora."""
        def mock_which(cmd):
            return cmd if cmd == "grub2-mkconfig" else None

        mocker.patch('shutil.which', side_effect=mock_which)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={'ID': 'fedora', 'ID_LIKE': ''})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub2/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")

        paths = GrubPaths()
        cmd = paths._detect_update_command()

        assert cmd == "grub2-mkconfig -o /boot/grub2/grub.cfg"

    def test_detect_update_command_arch_grub_mkconfig(self, mocker):
        """Test detecting grub-mkconfig on Arch Linux."""
        def mock_which(cmd):
            if cmd == "grub-mkconfig":
                return cmd
            return None

        mocker.patch('shutil.which', side_effect=mock_which)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={'ID': 'arch', 'ID_LIKE': ''})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")

        paths = GrubPaths()
        cmd = paths._detect_update_command()

        assert cmd == "grub-mkconfig -o /boot/grub/grub.cfg"

    def test_detect_update_command_rhel(self, mocker):
        """Test detecting update command on RHEL."""
        def mock_which(cmd):
            return cmd if cmd == "grub2-mkconfig" else None

        mocker.patch('shutil.which', side_effect=mock_which)
        mocker.patch.object(GrubPaths, '_parse_os_release',
                          return_value={'ID': 'rhel', 'ID_LIKE': 'fedora'})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub2/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")

        paths = GrubPaths()
        cmd = paths._detect_update_command()

        assert "grub2-mkconfig" in cmd

    def test_detect_update_command_fallback(self, mocker):
        """Test update command detection fallback."""
        mocker.patch('shutil.which', return_value=None)
        mocker.patch.object(GrubPaths, '_parse_os_release', return_value={})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")

        paths = GrubPaths()
        cmd = paths._detect_update_command()

        assert cmd == "update-grub"  # Default fallback

    def test_global_constants_set(self, mocker):
        """Test that global GRUB_FILE and GRUB_CFG_FILE constants are set."""
        from grub_settings_pkg import system

        assert system.GRUB_FILE == system.PATHS.grub_file
        assert system.GRUB_CFG_FILE == system.PATHS.grub_cfg

    def test_distro_info_logged(self, mocker, caplog):
        """Test that distro information is logged on initialization."""
        import logging
        caplog.set_level(logging.INFO)

        mocker.patch.object(GrubPaths, '_parse_os_release',
                          return_value={'ID': 'ubuntu', 'PRETTY_NAME': 'Ubuntu 22.04'})
        mocker.patch.object(GrubPaths, '_detect_grub_cfg', return_value="/boot/grub/grub.cfg")
        mocker.patch.object(GrubPaths, '_detect_efi_path', return_value="/boot/efi")
        mocker.patch.object(GrubPaths, '_detect_update_command', return_value="update-grub")

        paths = GrubPaths()

        assert "Distro: ubuntu" in caplog.text
        assert "GRUB Config: /boot/grub/grub.cfg" in caplog.text
        assert "EFI Path: /boot/efi" in caplog.text
        assert "Update Command: update-grub" in caplog.text

    def test_mint_uses_update_grub(self, mint_os_release, mocker):
        """Test that Linux Mint (Ubuntu-based) uses update-grub."""
        mocker.patch('shutil.which', side_effect=lambda x: x if x == "update-grub" else None)

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mint_os_release)):
                paths = GrubPaths()

        assert paths.update_cmd == "update-grub"

    def test_multiple_distro_like_values(self, mocker):
        """Test handling distros with multiple ID_LIKE values."""
        os_release_data = 'ID=pop\nID_LIKE="ubuntu debian"\nPRETTY_NAME="Pop!_OS"\n'

        mocker.patch('shutil.which', side_effect=lambda x: x if x == "update-grub" else None)
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=os_release_data)):
                paths = GrubPaths()
                info = paths._parse_os_release()

        assert info['ID_LIKE'] == 'ubuntu debian'
