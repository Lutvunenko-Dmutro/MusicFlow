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

        from core.i18n import _
        self.title_label = ctk.CTkLabel(self.header_frame, text=_("settings_title", "Settings"), font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"), text_color=("#111827", "#ffffff"))
        self.title_label.pack(side="left")

        # Container for settings cards
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._build_appearance_card()
        self._build_language_card()
        self._build_download_card()
        self._build_advanced_card()



    def _build_appearance_card(self):
        from core.i18n import _
        card = ctk.CTkFrame(self.container, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        card.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(card, text=_("set_appearance", "Appearance"), font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=("#111827", "#ffffff"))
        title.pack(anchor="w", padx=25, pady=(20, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=25, pady=(0, 20))

        lbl = ctk.CTkLabel(row, text=_("set_theme", "Theme"), font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl.pack(side="left")

        # Localized display names mapped to ctk values
        self._theme_map = {
            _("theme_dark",   "Dark"):   "Dark",
            _("theme_light",  "Light"):  "Light",
            _("theme_system", "System"): "System",
        }
        self._theme_reverse = {v: k for k, v in self._theme_map.items()}

        self.theme_menu = ctk.CTkOptionMenu(
            row, values=list(self._theme_map.keys()), command=self.change_theme,
            fg_color=("#F9FAFB", "#121212"), button_color=("#E5E7EB", "#333333"),
            button_hover_color=("#D1D5DB", "#4b5563"), text_color=("#111827", "#ffffff"),
            dropdown_fg_color=("#FFFFFF", "#1A1A1A"), dropdown_hover_color=("#F3F4F6", "#2A2A2A"),
            dropdown_text_color=("#111827", "#ffffff")
        )
        current = self.config.get("theme", "Dark")
        self.theme_menu.set(self._theme_reverse.get(current, current))
        self.theme_menu.pack(side="right")

    def _build_language_card(self):
        from core.i18n import I18nManager, _
        i18n = I18nManager.get_instance()
        
        card = ctk.CTkFrame(self.container, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        card.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(card, text=_("set_lang", "Language"), font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=("#111827", "#ffffff"))
        title.pack(anchor="w", padx=25, pady=(20, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=25, pady=(0, 10))

        lbl = ctk.CTkLabel(row, text=_("set_restart", "Restart required to apply changes"), font=ctk.CTkFont(family="Segoe UI", size=13), text_color=("#E52D27", "#ef4444"))
        lbl.pack(side="left")

        # Map language names back to codes
        self.lang_map = {v: k for k, v in i18n.available_langs.items()}
        current_lang_name = i18n.available_langs.get(i18n.current_lang, "English")

        self.lang_menu = ctk.CTkOptionMenu(
            row, values=list(i18n.available_langs.values()), command=self.change_language,
            fg_color=("#F9FAFB", "#121212"), button_color=("#E5E7EB", "#333333"), 
            button_hover_color=("#D1D5DB", "#4b5563"), text_color=("#111827", "#ffffff"),
            dropdown_fg_color=("#FFFFFF", "#1A1A1A"), dropdown_hover_color=("#F3F4F6", "#2A2A2A"), 
            dropdown_text_color=("#111827", "#ffffff")
        )
        self.lang_menu.set(current_lang_name)
        self.lang_menu.pack(side="right")

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=25, pady=(0, 20))
        
        btn_open = ctk.CTkButton(row2, text=_("set_lang_open", "Open translations folder"), width=120, height=35, corner_radius=8, fg_color=("#E5E7EB", "#2A2A2A"), hover_color=("#D1D5DB", "#3A3A3A"), text_color=("#111827", "#ffffff"), command=self.open_locales_folder)
        btn_open.pack(side="right")

    def change_language(self, choice):
        lang_code = self.lang_map.get(choice, "en")
        self.config["language"] = lang_code
        save_config(self.config)

    def open_locales_folder(self):
        from core.i18n import I18nManager
        folder = I18nManager.get_instance().locales_dir
        if os.name == 'nt':
            os.startfile(folder)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', folder))

    def _build_download_card(self):
        from core.i18n import _
        card = ctk.CTkFrame(self.container, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        card.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(card, text=_("set_downloads", "Downloads"), font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=("#111827", "#ffffff"))
        title.pack(anchor="w", padx=25, pady=(20, 10))

        # Folder
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=25, pady=(0, 15))

        lbl1 = ctk.CTkLabel(row1, text=_("set_location", "Download Location"), font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl1.pack(anchor="w")

        folder_inner = ctk.CTkFrame(row1, fg_color="transparent")
        folder_inner.pack(fill="x", pady=(5, 0))

        self.folder_entry = ctk.CTkEntry(folder_inner, height=40, font=ctk.CTkFont(family="Segoe UI", size=13))
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.folder_entry.insert(0, self.config.get("output_folder", ""))
        self.folder_entry.configure(state="disabled")

        btn_folder = ctk.CTkButton(folder_inner, text=_("set_btn_folder", "Change Folder"), width=120, height=40, corner_radius=8, fg_color=("#E5E7EB", "#2A2A2A"), hover_color=("#D1D5DB", "#3A3A3A"), text_color=("#111827", "#ffffff"), command=self.change_folder)
        btn_folder.pack(side="right")

        # Quality
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=25, pady=(15, 20))

        lbl2 = ctk.CTkLabel(row2, text=_("set_quality", "Default Audio Quality (kbps)"), font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl2.pack(side="left")

        self.quality_menu = ctk.CTkOptionMenu(
            row2, values=["320", "256", "192", "128"], command=self.change_quality,
            fg_color=("#F9FAFB", "#121212"), button_color=("#E5E7EB", "#333333"), 
            button_hover_color=("#D1D5DB", "#4b5563"), text_color=("#111827", "#ffffff"),
            dropdown_fg_color=("#FFFFFF", "#1A1A1A"), dropdown_hover_color=("#F3F4F6", "#2A2A2A"), 
            dropdown_text_color=("#111827", "#ffffff")
        )
        self.quality_menu.set(self.config.get("quality", "320"))
        self.quality_menu.pack(side="right")

    def _build_advanced_card(self):
        from core.i18n import _
        card = ctk.CTkFrame(self.container, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        card.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(card, text=_("set_advanced", "Advanced"), font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=("#111827", "#ffffff"))
        title.pack(anchor="w", padx=25, pady=(20, 10))

        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=25, pady=(0, 15))
        
        lbl1 = ctk.CTkLabel(row1, text=_("set_engine", "Download Engine (yt-dlp)"), font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl1.pack(side="left")

        self.update_btn = ctk.CTkButton(row1, text=_("set_btn_engine", "Update Engine"), width=120, height=35, corner_radius=8, fg_color=("#E5E7EB", "#2A2A2A"), hover_color=("#D1D5DB", "#3A3A3A"), text_color=("#111827", "#ffffff"), command=self.update_engine)
        self.update_btn.pack(side="right")

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=25, pady=(15, 15))

        lbl2 = ctk.CTkLabel(row2, text=_("set_clear_history", "Clear Download History\n(Does not delete MP3 files)"), justify="left", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl2.pack(side="left")

        btn_clear = ctk.CTkButton(row2, text=_("set_btn_clear_history", "Clear History"), width=120, height=35, corner_radius=8, fg_color="#E52D27", hover_color="#C0201E", command=self.clear_history)
        btn_clear.pack(side="right")
        
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=25, pady=(15, 20))

        lbl3 = ctk.CTkLabel(row3, text=_("set_sponsorblock_desc", "SponsorBlock\n(Remove intro, outro, sponsor segments)"), justify="left", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl3.pack(side="left")

        self.sponsor_switch = ctk.CTkSwitch(row3, text="", command=self.toggle_sponsorblock, progress_color="#E52D27")
        if self.config.get("use_sponsorblock", True):
            self.sponsor_switch.select()
        self.sponsor_switch.pack(side="right")



        row4 = ctk.CTkFrame(card, fg_color="transparent")
        row4.pack(fill="x", padx=25, pady=(15, 20))

        self.cache_lbl = ctk.CTkLabel(row4, text=_("set_cache", "Visualizer Cache\n(Currently {size} MB)").replace("{size}", "0.0"), justify="left", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        self.cache_lbl.pack(side="left")
        self.update_cache_label()

        self.btn_clear_cache = ctk.CTkButton(row4, text=_("set_btn_cache", "Clear Cache"), width=120, height=35, corner_radius=8, fg_color=("#D1D5DB", "#374151"), hover_color=("#FCA5A5", "#ef4444"), text_color=("#111827", "#ffffff"), command=self.clear_viz_cache)
        self.btn_clear_cache.pack(side="right")

        # Visualizer FPS row
        row5 = ctk.CTkFrame(card, fg_color="transparent")
        row5.pack(fill="x", padx=25, pady=(15, 20))
        lbl5 = ctk.CTkLabel(row5, text=_("set_fps", "Visualizer FPS (30 for weaker PCs)"), justify="left", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl5.pack(side="left")
        
        self.fps_menu = ctk.CTkOptionMenu(
            row5, values=["30", "60"], command=self.change_fps, width=120,
            fg_color=("#F9FAFB", "#121212"), button_color=("#E5E7EB", "#333333"), 
            button_hover_color=("#D1D5DB", "#4b5563"), text_color=("#111827", "#ffffff"),
            dropdown_fg_color=("#FFFFFF", "#1A1A1A"), dropdown_hover_color=("#F3F4F6", "#2A2A2A"), 
            dropdown_text_color=("#111827", "#ffffff")
        )
        self.fps_menu.set(str(self.config.get("viz_fps", "60")))
        self.fps_menu.pack(side="right")

        # Aria2c row
        row6 = ctk.CTkFrame(card, fg_color="transparent")
        row6.pack(fill="x", padx=25, pady=(15, 20))
        lbl6 = ctk.CTkLabel(row6, text=_("set_aria2c", "Use Aria2c for downloads\n(Requires aria2c to be installed)"), justify="left", font=ctk.CTkFont(family="Segoe UI", size=15), text_color=("#374151", "#d1d5db"))
        lbl6.pack(side="left")
        
        self.aria2c_switch = ctk.CTkSwitch(row6, text="", command=self.toggle_aria2c, progress_color="#E52D27")
        if self.config.get("use_aria2c", False):
            self.aria2c_switch.select()
        self.aria2c_switch.pack(side="right")

    def get_cache_size(self):
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        cache_dir = os.path.join(appdata, "YouTubeMusicPro", "viz_cache")
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

    def update_cache_label(self):
        from core.i18n import _
        cache_size = self.get_cache_size()
        display_size = 0.1 if 0 < cache_size < 0.05 else cache_size
        if hasattr(self, 'cache_lbl'):
            self.cache_lbl.configure(text=_("set_cache", "Visualizer Cache\n(Currently {size} MB)").replace("{size}", f"{display_size:.1f}"))

    def clear_viz_cache(self):
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        cache_dir = os.path.join(appdata, "YouTubeMusicPro", "viz_cache")
        if os.path.exists(cache_dir):
            try:
                for f in os.listdir(cache_dir):
                    fp = os.path.join(cache_dir, f)
                    if os.path.isfile(fp):
                        os.remove(fp)
            except Exception:
                pass
        self.update_cache_label()

    def toggle_sponsorblock(self):
        self.config["use_sponsorblock"] = bool(self.sponsor_switch.get())
        save_config(self.config)
        
    def change_fps(self, choice):
        self.config["viz_fps"] = choice
        save_config(self.config)
        
    def toggle_aria2c(self):
        self.config["use_aria2c"] = bool(self.aria2c_switch.get())
        save_config(self.config)

    def change_theme(self, display_choice):
        # Map localized label back to English value for ctk and config
        real = getattr(self, '_theme_map', {}).get(display_choice, display_choice)
        self.config["theme"] = real
        save_config(self.config)
        ctk.set_appearance_mode(real)

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
