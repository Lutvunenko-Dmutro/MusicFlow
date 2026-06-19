import os
import urllib.request

icons_dir = "icons"
os.makedirs(icons_dir, exist_ok=True)

icons = {
    "dashboard.png": "https://img.icons8.com/ios-filled/50/ffffff/home.png",
    "dashboard_active.png": "https://img.icons8.com/ios-filled/50/e52d27/home.png",
    "library.png": "https://img.icons8.com/ios-filled/50/ffffff/mac-folder.png",
    "play.png": "https://img.icons8.com/ios-filled/50/ffffff/play--v1.png",
    "settings.png": "https://img.icons8.com/ios-filled/50/ffffff/settings.png",
    "logo.png": "https://img.icons8.com/ios-filled/50/e52d27/apple-music.png",
    "music_placeholder.png": "https://img.icons8.com/ios-filled/80/444444/music.png"
}

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in icons.items():
    path = os.path.join(icons_dir, name)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response, open(path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Downloaded {name}")
    except Exception as e:
        print(f"Error downloading {name}: {e}")

print("Done.")
