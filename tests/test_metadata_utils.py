import pytest
from utils import metadata_utils

def test_clean_text_basic():
    assert metadata_utils.clean_text("Song Name") == "Song Name"

def test_clean_text_with_brackets():
    # Should remove (Official Video)
    assert metadata_utils.clean_text("Song Name (Official Video)") == "Song Name"
    assert metadata_utils.clean_text("Song Name [Lyric Video]") == "Song Name"

def test_clean_text_with_pipe():
    # Should remove anything after pipe
    assert metadata_utils.clean_text("Song Name | Official Audio") == "Song Name"

def test_clean_text_with_dash():
    # Should remove anything after " - "
    assert metadata_utils.clean_text("Artist - Song Name") == "Artist"

def test_clean_text_empty():
    assert metadata_utils.clean_text("") == ""
    assert metadata_utils.clean_text(None) == ""

def test_fetch_lrc_success(mocker):
    # Mock requests.get to return a fake JSON response
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"syncedLyrics": "[00:10.00] Test Lyrics"}]
    
    mocker.patch('requests.get', return_value=mock_response)
    
    lyrics = metadata_utils.fetch_lrc("Song", "Artist", "file")
    assert lyrics == "[00:10.00] Test Lyrics"

def test_fetch_lrc_failure(mocker):
    # Mock requests.get to fail
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    
    mocker.patch('requests.get', return_value=mock_response)
    
    lyrics = metadata_utils.fetch_lrc("Song", "Artist", "file")
    assert lyrics is None
