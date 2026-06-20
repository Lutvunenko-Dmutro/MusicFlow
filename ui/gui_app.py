import os
import sys
import subprocess
import customtkinter as ctk
from core.download_controller import DownloadController
from core.config_manager import load_config
from ui.app_setup import setup_ui, setup_bindings

ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        from utils.error_handler import set_app_instance
        set_app_instance(self)

        self.config = load_config()

        # Initialize I18n before any UI is built
        from core.i18n import I18nManager
        I18nManager.get_instance(self.config)

        ctk.set_appearance_mode(self.config.get("theme", "Dark"))

        self.title("Music Flow")
        self.geometry("1150x680")
        self.minsize(900, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.configure(fg_color=("#F3F4F6", "#121212"))

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
                # Fix for Windows Taskbar icon
                if os.name == 'nt':
                    import ctypes
                    myappid = 'dimamu.ytmusicdownloader.1.0'
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

        self.output_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.download_controller = DownloadController(self)

        setup_ui(self)

        from core.playlist_manager import PlaylistManager
        from core.preview_manager import PreviewManager
        self.playlist_manager = PlaylistManager(self.player_bar, self.output_folder)
        self.preview_manager  = PreviewManager(self)
        self.last_downloaded_file = None

        setup_bindings(self)

    # ── Navigation ──────────────────────────────────────────────────────────
    def hide_all_areas(self):
        for attr in ('main_area', 'right_column', 'library_area', 'history_area', 'settings_area'):
            if hasattr(self, attr):
                getattr(self, attr).grid_remove()

    def show_dashboard(self):
        self.hide_all_areas()
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        self.right_column.grid(row=0, column=2, sticky="nsew", padx=(10, 20), pady=20)
        self.reset_sidebar_buttons()
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
        if hasattr(self, 'settings_area') and hasattr(self.settings_area, 'update_cache_label'):
            self.settings_area.update_cache_label()
        self.settings_area.grid(row=0, column=1, columnspan=2, sticky="nsew", padx=20, pady=20)
        self.reset_sidebar_buttons()
        self.sidebar.btn_settings.configure(text_color="#E52D27", fg_color=("#E5E7EB", "#1A1A1A"))

    def reset_sidebar_buttons(self):
        default_color = ("#374151", "#d1d5db")
        for btn in (self.sidebar.btn_dashboard, self.sidebar.btn_library, self.sidebar.btn_history):
            btn.configure(text_color=default_color, fg_color="transparent")
        self.sidebar.btn_settings.configure(text_color=("#6B7280", "#9ca3af"), fg_color="transparent")

    # ── Playback shortcuts ───────────────────────────────────────────────────
    def play_specific_music(self, path):
        if os.path.exists(path):
            self.player_bar.load_and_play(path)

    def play_music(self):
        self.playlist_manager.play_initial()

    def play_next_song(self):
        self.playlist_manager.play_next()

    def play_prev_song(self):
        self.playlist_manager.play_prev()

    # ── UI helpers ───────────────────────────────────────────────────────────
    def update_status(self, text):
        if "Status:" not in text and text != "":
            text = f"Status: {text}"
        self.status_label.configure(text=text)

    def show_toast(self, message, toast_type="info"):
        from ui.components import ToastNotification
        ToastNotification.show(self, message, toast_type)

    def reset_ui(self):
        self.url_entry.configure(state="normal")
        self.paste_btn.configure(state="normal")
        self.download_btn.configure(state="disabled")
        self.url_entry.delete(0, 'end')
        self.main_area.preview_card.pack_forget()
        self.main_area.progress_card.pack_forget()
        self.main_area.welcome_frame.pack(fill="both", expand=True, pady=40)
        self.main_area.btn_cancel.configure(state="disabled")
        self.progressbar.set(0)
        for lbl, txt in [
            (self.main_area.size_label,  "Size: -"),
            (self.main_area.speed_label, "Speed: -"),
            (self.main_area.eta_label,   "ETA: -"),
        ]:
            lbl.configure(text=txt)
        self.main_area.prog_track_title.configure(text="Waiting...", text_color=("#374151", "#d1d5db"))
        self.main_area.prog_track_artist.configure(text="-", text_color=("#6B7280", "#9ca3af"))
        self.update_status("Status: Ready")

    def open_folder(self):
        if sys.platform == "win32":
            os.startfile(self.output_folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", self.output_folder])
        else:
            subprocess.Popen(["xdg-open", self.output_folder])

    def on_closing(self):
        try:
            import pygame
            pygame.mixer.quit()
        except Exception:
            pass
        self.destroy()
        sys.exit(0)

    def on_url_typing(self, event):
        if self.url_entry.cget("state") == "disabled":
            return
        if event.keysym in ('Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R', 'Super_L', 'Super_R', 'Print'):
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

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

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
