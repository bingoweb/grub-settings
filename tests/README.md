# GRUB Settings Test Suite

This directory contains the comprehensive test suite for GRUB Settings.

## Directory Structure

```
tests/
├── conftest.py                 # Shared pytest fixtures
├── fixtures/                   # Test data fixtures
│   ├── grub_configs/          # Sample GRUB configuration files
│   └── os_releases/           # Sample /etc/os-release files
├── unit/                       # Unit tests
│   ├── test_config.py         # Tests for config.py (GrubConfig, ConfigManager)
│   ├── test_system.py         # Tests for system.py (GrubPaths, distro detection)
│   └── test_utils.py          # Tests for utils.py (utility functions)
└── integration/                # Integration tests
    └── test_config_roundtrip.py  # Config read/modify/write tests
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=grub_settings_pkg --cov-report=term-missing
```

### Run specific test categories:
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/ -m integration

# Specific test file
pytest tests/unit/test_config.py

# Specific test function
pytest tests/unit/test_config.py::TestGrubConfig::test_parse_simple_values
```

### Generate HTML coverage report:
```bash
pytest --cov=grub_settings_pkg --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Coverage Goals

| Module | Target Coverage | Current Status |
|--------|----------------|----------------|
| `config.py` | 90%+ | ✅ Comprehensive tests |
| `system.py` | 85%+ | ✅ Comprehensive tests |
| `utils.py` | 80%+ | ✅ Comprehensive tests |
| `app.py` | 60%+ | 🚧 Needs UI mocking |
| Overall | 70%+ | 🎯 Target |

## Test Fixtures

### GRUB Configuration Fixtures
- `ubuntu_default.grub` - Standard Ubuntu GRUB config
- `fedora_default.grub` - Standard Fedora GRUB config
- `quoted_values.grub` - Tests various quoting styles
- `commented_options.grub` - Tests commented-out options
- `special_chars.grub` - Tests special characters ($, `, etc.)
- `minimal.grub` - Minimal configuration
- `empty.grub` - Empty/comments-only file

### OS Release Fixtures
- `ubuntu-22.04` - Ubuntu 22.04 LTS
- `fedora-39` - Fedora 39
- `arch` - Arch Linux
- `debian-12` - Debian 12 (Bookworm)
- `rhel-9` - Red Hat Enterprise Linux 9
- `linux-mint` - Linux Mint 21.2

## Writing New Tests

### Example unit test:
```python
def test_parse_simple_values(tmp_path, mocker):
    """Test parsing simple key=value pairs."""
    grub_file = tmp_path / "grub"
    grub_file.write_text("GRUB_DEFAULT=0\\nGRUB_TIMEOUT=5\\n")
    mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

    gc = GrubConfig()
    assert gc.get("GRUB_DEFAULT") == "0"
    assert gc.get("GRUB_TIMEOUT") == "5"
```

### Using fixtures:
```python
def test_load_ubuntu_fixture(ubuntu_grub_config, tmp_path, mocker):
    """Test loading Ubuntu default GRUB config."""
    grub_file = tmp_path / "grub"
    grub_file.write_text(ubuntu_grub_config)
    mocker.patch('grub_settings_pkg.config.GRUB_FILE', str(grub_file))

    gc = GrubConfig()
    assert gc.get("GRUB_DEFAULT") == "0"
```

## CI/CD Integration

Tests run automatically on:
- All pushes to `main` branch
- All pushes to branches starting with `claude/`
- All pull requests to `main`
- Before creating releases (tags starting with `v`)

### Coverage Requirements
- Minimum overall coverage: 50%
- Coverage reports uploaded to Codecov
- HTML coverage reports generated as artifacts

## Best Practices

1. **Use descriptive test names**: `test_parse_quoted_values_double_quotes`
2. **One assertion per test** (when possible): Helps identify exact failure
3. **Use fixtures**: Reuse common test data and setup
4. **Mock external dependencies**: File I/O, system calls, GTK widgets
5. **Test edge cases**: Empty files, missing files, permission errors
6. **Document test purpose**: Use docstrings to explain what's being tested

## Troubleshooting

### ModuleNotFoundError
Make sure you're running pytest from the project root:
```bash
cd /path/to/grub-settings
pytest
```

### Import errors
Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### GTK-related errors
Install system GTK dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1

# Fedora
sudo dnf install python3-gobject gtk4 libadwaita
```

## Contributing

When adding new features:
1. Write tests first (TDD approach recommended)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov`
4. Add new fixtures if needed
5. Update this README if adding new test categories
