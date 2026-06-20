import pytest
from utils import youtube_api

def test_get_preview_info_success(mocker):
    # Mock yt_dlp
    mock_ydl = mocker.MagicMock()
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {
        'title': 'Test Video',
        'uploader': 'Test Uploader',
        'thumbnail': 'http://fake.url/thumb.jpg',
        '_type': 'video'
    }
    mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
    
    # Mock requests for thumbnail
    mock_resp = mocker.Mock()
    mock_resp.status_code = 200
    mock_resp.content = b"fake image data"
    mocker.patch('requests.get', return_value=mock_resp)
    
    # Mock PIL Image to prevent crashing on fake image data
    mock_img = mocker.Mock()
    mock_img.size = (100, 100)
    mock_img.crop.return_value = mock_img
    mocker.patch('PIL.Image.open', return_value=mock_img)
    mocker.patch('customtkinter.CTkImage')
    
    # Track callbacks
    success_called = []
    error_called = []
    image_called = []
    
    def on_success(title, artist):
        success_called.append((title, artist))
        
    def on_error(t, m):
        error_called.append((t, m))
        
    def on_image(img):
        image_called.append(img)
        
    youtube_api.get_preview_info(
        "http://fake.url", "Single Track",
        on_success, on_error, on_image, "fake_path"
    )
    
    # Assertions
    assert len(success_called) == 1
    assert success_called[0] == ('Test Video', 'Test Uploader')
    assert len(error_called) == 0
    assert len(image_called) == 1

def test_get_preview_info_playlist(mocker):
    # Mock yt_dlp for a playlist
    mock_ydl = mocker.MagicMock()
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {
        'title': 'My Playlist',
        '_type': 'playlist',
        'playlist_count': 50
    }
    mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
    
    success_called = []
    
    def on_success(title, artist):
        success_called.append((title, artist))
        
    def on_error(t, m): pass
    def on_image(img): pass
        
    youtube_api.get_preview_info(
        "http://fake.url", "Playlist",
        on_success, on_error, on_image, "fake_path"
    )
    
    assert len(success_called) == 1
    # Uploader should be replaced with Playlist format
    assert success_called[0] == ('My Playlist', 'Playlist • 50 videos')

def test_get_preview_info_error(mocker):
    # Mock yt_dlp to throw an exception
    mock_ydl = mocker.MagicMock()
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = Exception("Failed")
    mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
    
    error_called = []
    def on_success(title, artist): pass
    def on_error(t, m): error_called.append((t, m))
    def on_image(img): pass
        
    youtube_api.get_preview_info(
        "http://fake.url", "Single Track",
        on_success, on_error, on_image, "fake_path"
    )
    
    assert len(error_called) == 1
    assert error_called[0][0] == "Video Unavailable / Error"
