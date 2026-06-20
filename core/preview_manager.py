import os
import threading

class PreviewManager:
    """Керує завантаженням та відображенням прев'ю відео з YouTube"""
    def __init__(self, app):
        self.app = app

    def trigger_preview(self, url):
        self.app.main_area.welcome_frame.pack_forget()
        self.app.main_area.preview_card.pack(fill="x", pady=(0, 15), padx=25)
        self.app.main_area.preview_title.configure(text="Fetching info...")
        self.app.main_area.preview_artist.configure(text="")
        threading.Thread(target=self.fetch_preview_info, args=(url,), daemon=True).start()

    def fetch_preview_info(self, url):
        from utils.youtube_api import get_preview_info
        mode = self.app.right_column.mode_dropdown.get()
        default_icon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "music_placeholder.png")
        
        def on_success(title, artist):
            self.app.after(0, lambda: self.app.main_area.preview_title.configure(text=title[:40]+"..." if len(title)>40 else title))
            self.app.after(0, lambda: self.app.main_area.preview_artist.configure(text=artist))
            self.app.after(0, lambda: self.app.main_area.download_btn.configure(state="normal"))
            
        def on_error(title, artist):
            self.app.after(0, lambda: self.app.main_area.preview_title.configure(text=title))
            self.app.after(0, lambda: self.app.main_area.preview_artist.configure(text=artist))
            self.app.after(0, lambda: self.app.main_area.download_btn.configure(state="disabled"))
            
        def on_image(photo):
            self.app.after(0, lambda: self.app.main_area.thumbnail_label.configure(image=photo, text=""))
            
        get_preview_info(url, mode, on_success, on_error, on_image, default_icon)
