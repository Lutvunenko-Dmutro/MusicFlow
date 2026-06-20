import customtkinter as ctk
import tkinter as tk
import threading
import os
import sys
import subprocess
from ui.sidebar import  SidebarFrame
from ui.main_area import  MainAreaFrame
from ui.right_column import  RightColumnFrame
from ui.player_bar import  PlayerBarFrame
from ui.library import  LibraryFrame
from ui.settings import  SettingsFrame
from core.download_controller import  DownloadController
from core.config_manager import  load_config
ctk.set_default_color_theme("blue")  # Сині акценти

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = load_config()
        ctk.set_appearance_mode(self.config.get("theme", "Dark"))

        self.title("YT Music Downloader")
        self.geometry("1150x680")
        self.minsize(900, 600)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set App Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        
        self.last_downloaded_file = None
        self.output_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Встановлюємо фон вікна з підтримкою світлої/темної теми
        self.configure(fg_color=("#F3F4F6", "#121212"))
        
        self.download_controller = DownloadController(self)
        
        self._setup_ui()
        from core.playlist_manager import PlaylistManager
        from core.preview_manager import PreviewManager
        
        self.playlist_manager = PlaylistManager(self.player_bar, self.output_folder)
        self.preview_manager = PreviewManager(self)
        self.last_downloaded_file = None # Will be handled by playlist_manager
        
        self._setup_bindings()

    def _setup_ui(self):
        # Configure layout: 2 rows, 3 columns
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0) # For player bar
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main content (takes all remaining space)
        self.grid_columnconfigure(2, weight=0, minsize=320) # Right column (FIXED width, no jitter)

        self.output_folder = self.config.get("output_folder", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "My_Music"))
        os.makedirs(self.output_folder, exist_ok=True)
        self.sidebar = SidebarFrame(self, self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.main_area = MainAreaFrame(self, self)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)

        self.right_column = RightColumnFrame(self, self)
        self.right_column.grid(row=0, column=2, sticky="nsew", padx=(10, 20), pady=20)
        
        self.library_area = LibraryFrame(self, self)
        from ui.history import HistoryFrame
        self.history_area = HistoryFrame(self, self)
        self.settings_area = SettingsFrame(self, self)
        # Not gridded initially
        
        self.player_bar = PlayerBarFrame(self, self)
        self.player_bar.grid(row=1, column=0, columnspan=3, sticky="sew", padx=0, pady=0)

        # Встановлюємо змінні для легкого доступу з інших методів
        self.url_entry = self.main_area.url_entry
        self.paste_btn = self.main_area.paste_btn
        self.download_btn = self.main_area.download_btn
        self.progressbar = self.main_area.progressbar
        self.status_label = self.main_area.status_label
        self.eta_label = self.main_area.eta_label
        self.speed_label = self.main_area.speed_label

        # Right-click context menu
        self.context_menu = tk.Menu(self, tearoff=False, bg="#2b2b2b", fg="white", font=("Segoe UI", 11))
        self.context_menu.add_command(label="Вставити", command=self.paste_from_clipboard)
        self.context_menu.add_command(label="Очистити", command=lambda: self.url_entry.delete(0, 'end'))

    def _setup_bindings(self):
        self.url_entry.focus_set()
        
        # Таймер для перевірки введеного тексту (щоб не спамити API на кожну літеру)
        self.typing_timer = None
        self.url_entry.bind("<KeyRelease>", self.on_url_typing)
        
        self.url_entry.bind("<Return>", lambda e: self.download_controller.start_download_thread() if self.download_btn.cget("state") == "normal" else None)
        self.url_entry.bind("<Control-KeyPress>", self.handle_ctrl_v)
        self.url_entry.bind("<Button-3>", self.show_context_menu)
        self.main_area.btn_finish.configure(command=self.reset_ui)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def on_url_typing(self, event):
        # Ігноруємо натискання спец-клавіш (Control, Shift тощо)
        if event.keysym in ('Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R'):
            return
            
        url = self.url_entry.get().strip()
        if not url:
            self.main_area.download_btn.configure(state="disabled")
            self.main_area.preview_card.pack_forget()
            return

        if self.typing_timer is not None:
            self.after_cancel(self.typing_timer)
            
        self.main_area.download_btn.configure(state="disabled")
        self.typing_timer = self.after(800, lambda: self.preview_manager.trigger_preview(url))



    def handle_ctrl_v(self, event):
        if getattr(event, 'keysym', '').lower() == 'v' or event.keycode == 86:
            self.paste_from_clipboard()
            return "break"

    def update_status(self, text):
        if "Status:" not in text and text != "":
            text = f"Status: {text}"
        self.status_label.configure(text=text)

    def show_toast(self, message, toast_type="info"):
        from ui.components import ToastNotification
        ToastNotification.show(self, message, toast_type)

    def on_closing(self):
        try:
            import pygame
            pygame.mixer.quit()
        except Exception:
            pass
        self.destroy()
        sys.exit(0)

    def reset_ui(self):
        self.url_entry.configure(state="normal")
        self.paste_btn.configure(state="normal")
        self.download_btn.configure(state="disabled")
        self.url_entry.delete(0, 'end')
        self.main_area.preview_card.pack_forget()
        self.main_area.progress_card.pack_forget()
        self.main_area.welcome_frame.pack(fill="both", expand=True, pady=40)
        self.main_area.btn_finish.configure(state="disabled")
        self.main_area.btn_cancel.configure(state="disabled")
        self.progressbar.set(0)
        self.main_area.size_label.configure(text="Size: -")
        self.main_area.speed_label.configure(text="Speed: -")
        self.main_area.eta_label.configure(text="ETA: -")
        self.main_area.prog_track_title.configure(text="Waiting...", text_color=("#374151", "#d1d5db"))
        self.main_area.prog_track_artist.configure(text="-", text_color=("#6B7280", "#9ca3af"))
        self.update_status("Status: Ready")

    def play_specific_music(self, path):
        if os.path.exists(path):
            self.player_bar.load_and_play(path)

    def hide_all_areas(self):
        if hasattr(self, 'main_area'): self.main_area.grid_remove()
        if hasattr(self, 'right_column'): self.right_column.grid_remove()
        if hasattr(self, 'library_area'): self.library_area.grid_remove()
        if hasattr(self, 'history_area'): self.history_area.grid_remove()
        if hasattr(self, 'settings_area'): self.settings_area.grid_remove()

    def show_dashboard(self):
        self.hide_all_areas()
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        self.right_column.grid(row=0, column=2, sticky="nsew", padx=(10, 20), pady=20)
        self.reset_sidebar_buttons()
        # Встановлюємо активний колір для тексту (наприклад червоний або білий)
        self.sidebar.btn_dashboard.configure(text_color="#E52D27", fg_color=("#E5E7EB", "#1A1A1A"))

    def show_library(self):
        self.hide_all_areas()
        self.library_area.load_library()
        self.library_area.grid(row=0, column=1, columnspan=2, sticky="nsew", padx=20, pady=20)
        self.reset_sidebar_buttons()
        self.sidebar.btn_library.configure(text_color="#E52D27", fg_color=("#E5E7EB", "#1A1A1A"))

    def show_history(self):
        self.hide_all_areas()
        self.history_area.load_history()
        self.history_area.grid(row=0, column=1, columnspan=2, sticky="nsew", padx=20, pady=20)
        self.reset_sidebar_buttons()
        self.sidebar.btn_history.configure(text_color="#E52D27", fg_color=("#E5E7EB", "#1A1A1A"))

    def show_settings(self):
        self.hide_all_areas()
        self.settings_area.grid(row=0, column=1, columnspan=2, sticky="nsew", padx=20, pady=20)
        self.reset_sidebar_buttons()
        self.sidebar.btn_settings.configure(text_color="#E52D27", fg_color=("#E5E7EB", "#1A1A1A"))

    def reset_sidebar_buttons(self):
        # Повертаємо всім кнопкам стандартний колір
        default_color = ("#374151", "#d1d5db")
        default_fg = "transparent"
        self.sidebar.btn_dashboard.configure(text_color=default_color, fg_color=default_fg)
        self.sidebar.btn_library.configure(text_color=default_color, fg_color=default_fg)
        self.sidebar.btn_history.configure(text_color=default_color, fg_color=default_fg)
        self.sidebar.btn_settings.configure(text_color=("#6B7280", "#9ca3af"), fg_color=default_fg)

    def open_folder(self):
        if sys.platform == "win32":
            os.startfile(self.output_folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", self.output_folder])
        else:
            subprocess.Popen(["xdg-open", self.output_folder])

    def play_music(self):
        self.playlist_manager.play_initial()

    def play_next_song(self):
        self.playlist_manager.play_next()

    def play_prev_song(self):
        self.playlist_manager.play_prev()

    def paste_from_clipboard(self):
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text:
                self.url_entry.delete(0, 'end')
                self.url_entry.insert(0, clipboard_text)
                self.main_area.download_btn.configure(state="disabled")
                self.preview_manager.trigger_preview(clipboard_text)
        except Exception:
            self.update_status("⚠️ Не вдалося прочитати буфер обміну")



