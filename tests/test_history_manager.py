import os
import json
import pytest
import history_manager

@pytest.fixture
def mock_history_file(tmp_path, mocker):
    test_hist_path = tmp_path / "test_history.json"
    mocker.patch('history_manager.HISTORY_JSON_FILE', str(test_hist_path))
    return test_hist_path

def test_get_json_history_empty(mock_history_file):
    assert history_manager.get_json_history() == []

def test_add_to_json_history(mock_history_file):
    history_manager.add_to_json_history("Test Song", "Test Artist", "http://test", "C:/test.mp3")
    history = history_manager.get_json_history()
    
    assert len(history) == 1
    assert history[0]["title"] == "Test Song"
    assert history[0]["artist"] == "Test Artist"
    assert history[0]["filepath"] == "C:/test.mp3"

def test_clear_json_history(mock_history_file):
    history_manager.add_to_json_history("Test", "Test", "url", "path")
    assert os.path.exists(mock_history_file)
    
    history_manager.clear_json_history()
    assert not os.path.exists(mock_history_file)
    assert history_manager.get_json_history() == []

def test_history_limit(mock_history_file):
    # Add 205 items
    for i in range(205):
        history_manager.add_to_json_history(f"Song {i}", "Artist", "url", "path")
    
    history = history_manager.get_json_history()
    # Should be limited to 200
    assert len(history) == 200
    # The most recent should be at index 0 (Song 204)
    assert history[0]["title"] == "Song 204"

def test_delete_history_files(mocker):
    # Mock os.path.exists to pretend files exist
    mocker.patch('os.path.exists', return_value=True)
    mock_remove = mocker.patch('os.remove')
    
    # Test deleting mp3 and associated lrc, jpg, webp
    history_manager.delete_history_files("C:/fake/song.mp3")
    
    # Check that remove was called for mp3 and other extensions
    removed_files = [call[0][0] for call in mock_remove.call_args_list]
    assert "C:/fake/song.mp3" in removed_files
    assert "C:/fake/song.lrc" in removed_files
    assert "C:/fake/song.jpg" in removed_files
    assert "C:/fake/song.webp" in removed_files
