import customtkinter as ctk
import os
import threading
import subprocess
from customtkinter import filedialog
from core.config_manager import  load_config, save_config

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=("#F3F4F6", "#121212"), **kwargs)
        self.app = app
        self.config = load_config()

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(30, 20))

        self.title_label = ctk.CTkLabel(self.header_frame, text="Settings", font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"), text_color=("#111827", "#ffffff"))
        self.title_label.pack(side="left")

        # Container for settings cards
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._build_appearance_card()
        self._build_download_card()
        self._build_advanced_card()

    def _build_appearance_card(self):
        card = ctk.CTkFrame(self.container, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        card.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(card, text="Appearance", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=("#111827", "#ffffff"))
        title.pack(anchor="w", padx=25, pady=(20, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=25, pady=(0, 20))

        lbl = ctk.CTkLabel(row, text="Theme", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl.pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(row, values=["Dark", "Light", "System"], command=self.change_theme)
        self.theme_menu.set(self.config.get("theme", "Dark"))
        self.theme_menu.pack(side="right")

    def _build_download_card(self):
        card = ctk.CTkFrame(self.container, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        card.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(card, text="Downloads", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=("#111827", "#ffffff"))
        title.pack(anchor="w", padx=25, pady=(20, 10))

        # Folder
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=25, pady=(0, 15))

        lbl1 = ctk.CTkLabel(row1, text="Download Location", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl1.pack(anchor="w")

        folder_inner = ctk.CTkFrame(row1, fg_color="transparent")
        folder_inner.pack(fill="x", pady=(5, 0))

        self.folder_entry = ctk.CTkEntry(folder_inner, height=40, font=ctk.CTkFont(family="Segoe UI", size=13))
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.folder_entry.insert(0, self.config.get("output_folder", ""))
        self.folder_entry.configure(state="disabled")

        btn_folder = ctk.CTkButton(folder_inner, text="Change Folder", width=120, height=40, corner_radius=8, fg_color=("#E5E7EB", "#2A2A2A"), hover_color=("#D1D5DB", "#3A3A3A"), text_color=("#111827", "#ffffff"), command=self.change_folder)
        btn_folder.pack(side="right")

        # Quality
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=25, pady=(15, 20))

        lbl2 = ctk.CTkLabel(row2, text="Default Audio Quality (kbps)", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl2.pack(side="left")

        self.quality_menu = ctk.CTkOptionMenu(row2, values=["320", "256", "192", "128"], command=self.change_quality)
        self.quality_menu.set(self.config.get("quality", "320"))
        self.quality_menu.pack(side="right")

    def _build_advanced_card(self):
        card = ctk.CTkFrame(self.container, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        card.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(card, text="Advanced", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=("#111827", "#ffffff"))
        title.pack(anchor="w", padx=25, pady=(20, 10))

        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=25, pady=(0, 15))
        
        lbl1 = ctk.CTkLabel(row1, text="Download Engine (yt-dlp)", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl1.pack(side="left")

        self.update_btn = ctk.CTkButton(row1, text="Update Engine", width=120, height=35, corner_radius=8, fg_color=("#E5E7EB", "#2A2A2A"), hover_color=("#D1D5DB", "#3A3A3A"), text_color=("#111827", "#ffffff"), command=self.update_engine)
        self.update_btn.pack(side="right")

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=25, pady=(15, 15))

        lbl2 = ctk.CTkLabel(row2, text="Clear Download History\n(Does not delete MP3 files)", justify="left", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl2.pack(side="left")

        btn_clear = ctk.CTkButton(row2, text="Clear History", width=120, height=35, corner_radius=8, fg_color="#E52D27", hover_color="#C0201E", command=self.clear_history)
        btn_clear.pack(side="right")
        
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=25, pady=(15, 20))

        lbl3 = ctk.CTkLabel(row3, text="SponsorBlock\n(Remove intro, outro, sponsor segments)", justify="left", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl3.pack(side="left")

        self.sponsor_switch = ctk.CTkSwitch(row3, text="", command=self.toggle_sponsorblock, progress_color="#E52D27")
        if self.config.get("use_sponsorblock", True):
            self.sponsor_switch.select()
        self.sponsor_switch.pack(side="right")

        row4 = ctk.CTkFrame(card, fg_color="transparent")
        row4.pack(fill="x", padx=25, pady=(15, 20))

        cache_size = self.get_cache_size()
        self.cache_lbl = ctk.CTkLabel(row4, text=f"Visualizer Cache\n(Currently {cache_size:.1f} MB)", justify="left", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        self.cache_lbl.pack(side="left")

        self.btn_clear_cache = ctk.CTkButton(row4, text="Clear Cache", width=120, height=35, corner_radius=8, fg_color=("#D1D5DB", "#374151"), hover_color=("#FCA5A5", "#ef4444"), text_color=("#111827", "#ffffff"), command=self.clear_viz_cache)
        self.btn_clear_cache.pack(side="right")

    def get_cache_size(self):
        cache_dir = ".viz_cache"
        if not os.path.exists(cache_dir):
            return 0
        total = 0
        try:
            for f in os.listdir(cache_dir):
                fp = os.path.join(cache_dir, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
        except Exception:
            pass
        return total / (1024 * 1024)

    def clear_viz_cache(self):
        cache_dir = ".viz_cache"
        if os.path.exists(cache_dir):
            try:
                for f in os.listdir(cache_dir):
                    fp = os.path.join(cache_dir, f)
                    if os.path.isfile(fp):
                        os.remove(fp)
            except Exception:
                pass
        self.cache_lbl.configure(text=f"Visualizer Cache\n(Currently 0.0 MB)")

    def toggle_sponsorblock(self):
        self.config["use_sponsorblock"] = bool(self.sponsor_switch.get())
        save_config(self.config)

    def change_theme(self, choice):
        self.config["theme"] = choice
        save_config(self.config)
        ctk.set_appearance_mode(choice)

    def change_folder(self):
        folder = filedialog.askdirectory(initialdir=self.config.get("output_folder"))
        if folder:
            self.config["output_folder"] = folder
            save_config(self.config)
            self.folder_entry.configure(state="normal")
            self.folder_entry.delete(0, 'end')
            self.folder_entry.insert(0, folder)
            self.folder_entry.configure(state="disabled")
            self.app.output_folder = folder
            
            if hasattr(self.app, 'right_column') and hasattr(self.app.right_column, 'folder_entry'):
                self.app.right_column.folder_entry.configure(state="normal")
                self.app.right_column.folder_entry.delete(0, 'end')
                self.app.right_column.folder_entry.insert(0, folder)
                self.app.right_column.folder_entry.configure(state="disabled")

    def change_quality(self, choice):
        self.config["quality"] = choice
        save_config(self.config)

    def clear_history(self):
        try:
            from core.history_manager import clear_history_data
            clear_history_data()
            if hasattr(self.app, 'right_column'):
                self.app.right_column.load_history()
            if hasattr(self.app, 'library_area'):
                self.app.library_area.load_library()
        except Exception:
            pass

    def update_engine(self):
        self.update_btn.configure(state="disabled", text="Updating...")
        def _update():
            try:
                subprocess.run(["python", "-m", "pip", "install", "-U", "yt-dlp"], check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                self.app.after(0, lambda: self.update_btn.configure(state="normal", text="Updated!"))
                self.app.after(3000, lambda: self.update_btn.configure(text="Update Engine"))
            except Exception as e:
                self.app.after(0, lambda: self.update_btn.configure(state="normal", text="Failed"))
        threading.Thread(target=_update, daemon=True).start()
