import os
import json
import pytest
from core import config_manager

# Fixture to safely replace the global CONFIG_FILE path during tests
@pytest.fixture
def mock_config_file(tmp_path, mocker):
    test_config_path = tmp_path / "test_config.json"
    mocker.patch('core.config_manager.CONFIG_FILE', str(test_config_path))
    return test_config_path

def test_load_config_no_file(mock_config_file):
    # Test loading when no file exists (should return default config)
    assert not os.path.exists(mock_config_file)
    config = config_manager.load_config()
    assert config == config_manager.DEFAULT_CONFIG

def test_save_and_load_config(mock_config_file):
    # Test saving a custom config and loading it back
    custom_config = config_manager.DEFAULT_CONFIG.copy()
    custom_config["theme"] = "Light"
    custom_config["quality"] = "192"
    
    config_manager.save_config(custom_config)
    assert os.path.exists(mock_config_file)
    
    loaded_config = config_manager.load_config()
    assert loaded_config["theme"] == "Light"
    assert loaded_config["quality"] == "192"

def test_load_config_corrupted_file(mock_config_file):
    # Test behavior when config file contains invalid JSON
    with open(mock_config_file, "w", encoding="utf-8") as f:
        f.write("{invalid_json: 123")
    
    config = config_manager.load_config()
    # Should fallback to default config instead of crashing
    assert config == config_manager.DEFAULT_CONFIG
