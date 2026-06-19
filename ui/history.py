import customtkinter as ctk
import os
import webbrowser
from PIL import Image

class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.title_lbl = ctk.CTkLabel(self.header_frame, text="Download History", font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"), text_color=("#111827", "#ffffff"))
        self.title_lbl.pack(side="left")

        self.clear_btn = ctk.CTkButton(self.header_frame, text="Clear History", fg_color=("#D1D5DB", "#374151"), hover_color=("#FCA5A5", "#ef4444"), text_color=("#111827", "#ffffff"), font=ctk.CTkFont(size=14, weight="bold"), width=120, height=36, corner_radius=8, command=self.clear_history)
        self.clear_btn.pack(side="right")

        # Table Header
        self.table_header = ctk.CTkFrame(self, fg_color=("#E5E7EB", "#1f2937"), corner_radius=8)
        self.table_header.pack(fill="x", padx=30, pady=(0, 10))
        
        ctk.CTkLabel(self.table_header, text="TITLE", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#6B7280", "#9ca3af"), anchor="w", width=300).pack(side="left", padx=(20, 10), pady=8)
        ctk.CTkLabel(self.table_header, text="ARTIST", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#6B7280", "#9ca3af"), anchor="w", width=200).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(self.table_header, text="DATE DOWNLOADED", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#6B7280", "#9ca3af"), anchor="w", width=150).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(self.table_header, text="ACTION", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#6B7280", "#9ca3af"), anchor="e").pack(side="right", padx=30, pady=8)

        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        self.placeholder_img = ctk.CTkImage(light_image=Image.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "music_placeholder.png")), size=(40, 40))
        
        self.load_history()

    def load_history(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        from core.history_manager import get_json_history
        history_data = get_json_history()

        if not history_data:
            ctk.CTkLabel(self.scroll_frame, text="Your download history is empty.", font=ctk.CTkFont(size=16), text_color=("#6B7280", "#6b7280")).pack(pady=50)
            return

        for i, item in enumerate(history_data):
            bg_color = ("#F9FAFB", "#18181b") if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self.scroll_frame, fg_color=bg_color, corner_radius=8)
            row.pack(fill="x", pady=2)

            # Icon
            ctk.CTkLabel(row, image=self.placeholder_img, text="", fg_color=("#E5E7EB", "#222222"), corner_radius=6).pack(side="left", padx=(10, 15), pady=8)

            # Title
            title = item.get("title", "Unknown Title")
            if len(title) > 35: title = title[:32] + "..."
            ctk.CTkLabel(row, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=("#111827", "#f3f4f6"), anchor="w", width=265).pack(side="left", padx=10)

            # Artist
            artist = item.get("artist", "Unknown Artist")
            if len(artist) > 25: artist = artist[:22] + "..."
            ctk.CTkLabel(row, text=artist, font=ctk.CTkFont(size=13), text_color=("#6B7280", "#9ca3af"), anchor="w", width=200).pack(side="left", padx=10)

            # Date
            date_str = item.get("timestamp", "Unknown")
            ctk.CTkLabel(row, text=date_str, font=ctk.CTkFont(size=13), text_color=("#9CA3AF", "#6b7280"), anchor="w", width=150).pack(side="left", padx=10)

            # Actions (URL, Play, Delete, Redownload)
            url = item.get("url", "")
            if url:
                ctk.CTkButton(row, text="🔗 URL", width=60, height=28, fg_color="transparent", border_width=1, border_color=("#D1D5DB", "#374151"), text_color=("#6B7280", "#9ca3af"), hover_color=("#F3F4F6", "#1f2937"), command=lambda u=url: webbrowser.open(u)).pack(side="right", padx=(5, 10))
            
            filepath = item.get("filepath", "")
            if filepath and os.path.exists(filepath) and filepath.endswith(".mp3"):
                ctk.CTkButton(row, text="▶ Play", width=60, height=28, fg_color="#E52D27", hover_color="#c0241f", text_color="#ffffff", command=lambda p=filepath: self.app.play_specific_music(p)).pack(side="right", padx=5)
                ctk.CTkButton(row, text="🗑", width=28, height=28, fg_color="transparent", hover_color=("#FCA5A5", "#5a1818"), text_color="#ef4444", command=lambda p=filepath: self.delete_file(p)).pack(side="right", padx=5)
            else:
                if url:
                    ctk.CTkButton(row, text="⬇ Redownload", width=100, height=28, fg_color=("#D1D5DB", "#1f2937"), hover_color=("#9CA3AF", "#374151"), text_color=("#111827", "#ffffff"), command=lambda u=url: self.redownload(u)).pack(side="right", padx=5)

    def redownload(self, url):
        self.app.show_dashboard()
        self.app.url_entry.delete(0, 'end')
        self.app.url_entry.insert(0, url)
        self.app.trigger_preview(url)

    def delete_file(self, filepath):
        from core.history_manager import delete_history_files
        try:
            delete_history_files(filepath)
        except Exception:
            pass
        self.load_history()

    def clear_history(self):
        from core.history_manager import clear_json_history
        clear_json_history()
        self.load_history()
