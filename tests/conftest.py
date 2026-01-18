"""Shared pytest fixtures for all tests."""
import os
import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def grub_configs_dir(fixtures_dir):
    """Return the path to the GRUB config fixtures directory."""
    return fixtures_dir / "grub_configs"


@pytest.fixture
def os_releases_dir(fixtures_dir):
    """Return the path to the os-release fixtures directory."""
    return fixtures_dir / "os_releases"


@pytest.fixture
def ubuntu_grub_config(grub_configs_dir):
    """Load Ubuntu default GRUB config."""
    return (grub_configs_dir / "ubuntu_default.grub").read_text()


@pytest.fixture
def fedora_grub_config(grub_configs_dir):
    """Load Fedora default GRUB config."""
    return (grub_configs_dir / "fedora_default.grub").read_text()


@pytest.fixture
def quoted_values_config(grub_configs_dir):
    """Load GRUB config with various quoting styles."""
    return (grub_configs_dir / "quoted_values.grub").read_text()


@pytest.fixture
def commented_options_config(grub_configs_dir):
    """Load GRUB config with commented options."""
    return (grub_configs_dir / "commented_options.grub").read_text()


@pytest.fixture
def special_chars_config(grub_configs_dir):
    """Load GRUB config with special characters."""
    return (grub_configs_dir / "special_chars.grub").read_text()


@pytest.fixture
def minimal_grub_config(grub_configs_dir):
    """Load minimal GRUB config."""
    return (grub_configs_dir / "minimal.grub").read_text()


@pytest.fixture
def empty_grub_config(grub_configs_dir):
    """Load empty GRUB config."""
    return (grub_configs_dir / "empty.grub").read_text()


@pytest.fixture
def ubuntu_os_release(os_releases_dir):
    """Load Ubuntu os-release file."""
    return (os_releases_dir / "ubuntu-22.04").read_text()


@pytest.fixture
def fedora_os_release(os_releases_dir):
    """Load Fedora os-release file."""
    return (os_releases_dir / "fedora-39").read_text()


@pytest.fixture
def arch_os_release(os_releases_dir):
    """Load Arch Linux os-release file."""
    return (os_releases_dir / "arch").read_text()


@pytest.fixture
def debian_os_release(os_releases_dir):
    """Load Debian os-release file."""
    return (os_releases_dir / "debian-12").read_text()


@pytest.fixture
def rhel_os_release(os_releases_dir):
    """Load RHEL os-release file."""
    return (os_releases_dir / "rhel-9").read_text()


@pytest.fixture
def mint_os_release(os_releases_dir):
    """Load Linux Mint os-release file."""
    return (os_releases_dir / "linux-mint").read_text()


@pytest.fixture
def mock_grub_file(tmp_path, mocker):
    """Create a temporary GRUB file and mock the GRUB_FILE constant."""
    grub_file = tmp_path / "grub"

    # Mock the GRUB_FILE in the config module
    mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

    return grub_file


@pytest.fixture
def mock_os_release(tmp_path, mocker):
    """Create a temporary os-release file."""
    os_release_file = tmp_path / "os-release"

    # Mock os.path.exists for /etc/os-release
    original_exists = os.path.exists

    def mock_exists(path):
        if path == "/etc/os-release":
            return os_release_file.exists()
        return original_exists(path)

    mocker.patch('os.path.exists', side_effect=mock_exists)

    # Mock file opening for os-release
    original_open = open

    def mock_open(path, *args, **kwargs):
        if path == "/etc/os-release":
            return original_open(str(os_release_file), *args, **kwargs)
        return original_open(path, *args, **kwargs)

    mocker.patch('builtins.open', side_effect=mock_open)

    return os_release_file
