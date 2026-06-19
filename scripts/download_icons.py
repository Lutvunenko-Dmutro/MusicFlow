import os
import urllib.request

icons_dir = "icons"
os.makedirs(icons_dir, exist_ok=True)

icons = {
    "dashboard.png": "https://img.icons8.com/ios-filled/50/ffffff/dashboard.png",
    "library.png": "https://img.icons8.com/ios-filled/50/ffffff/folder-invoices.png",
    "play.png": "https://img.icons8.com/ios-filled/50/ffffff/play--v1.png",
    "settings.png": "https://img.icons8.com/ios-filled/50/ffffff/settings.png"
}

print("Downloading icons...")
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
