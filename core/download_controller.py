import threading
import os

class DownloadController:
    def __init__(self, app):
        self.app = app
        self.current_download_process = None
        self.is_download_cancelled = False

    def start_download_thread(self):
        url = self.app.url_entry.get().strip()
        # Отримуємо налаштування з правого меню та глобальних налаштувань
        from core.i18n import _
        is_playlist = "list=" in url and "v=" not in url
        qual = self.app.config.get("quality", "320")
        embed_lrc = self.app.right_column.lyrics_switch.get()

        if not url:
            self.app.update_status(_("status_enter_url", "Enter a URL!"))
            return

        # Setup progress preview
        self.app.main_area.welcome_frame.pack_forget()
        self.app.main_area.preview_card.pack_forget()
        self.app.main_area.progress_card.pack(fill="x", pady=(0, 20), padx=25)
        
        thumb = self.app.main_area.thumbnail_label.cget("image")
        if thumb:
            self.app.main_area.prog_thumb.configure(image=thumb)
        self.app.main_area.prog_track_title.configure(text=self.app.main_area.preview_title.cget("text"), text_color="#d1d5db")
        self.app.main_area.prog_track_artist.configure(text=self.app.main_area.preview_artist.cget("text"), text_color="#9ca3af")

        # Disable buttons to prevent spam
        self.app.url_entry.configure(state="disabled")
        self.app.download_btn.configure(state="disabled")
        self.app.paste_btn.configure(state="disabled")
        
        # Show progress bar and reset status
        self.app.progressbar.set(0)
        self.app.main_area.progress_percent_label.configure(text="0%")
        self.app.main_area.size_label.configure(text="-")
        from core.i18n import _
        self.app.update_status(_("status_starting", "Status: Starting..."))

        # Setup Cancel button
        self.is_download_cancelled = False
        self.app.main_area.btn_cancel.configure(state="normal", text_color="#ef4444", command=self.cancel_download)

        # Run download in a separate thread so GUI doesn't freeze
        thread = threading.Thread(target=self.download_music, args=(url, self.app.output_folder, is_playlist, embed_lrc), daemon=True)
        thread.start()

    def cancel_download(self):
        self.is_download_cancelled = True
        self.app.main_area.btn_cancel.configure(state="disabled")
        from core.i18n import _
        self.app.update_status(_("status_cancelling", "Cancelling..."))
        
        if self.current_download_process:
            import subprocess
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_download_process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.current_download_process.terminate()
            except Exception:
                pass

        def cleanup_garbage():
            import time, glob, os
            time.sleep(1) # wait for process to fully die
            try:
                folder = self.app.output_folder
                for ext in ('*.part', '*.ytdl', '*.temp', '*.f251', '*.f140', '*.webm'):
                    for f in glob.glob(os.path.join(folder, ext)):
                        try:
                            # Only delete if it's very recent (created/modified in the last 5 minutes)
                            if time.time() - os.path.getmtime(f) < 300:
                                os.remove(f)
                        except:
                            pass
            except:
                pass
                
        threading.Thread(target=cleanup_garbage, daemon=True).start()

    def download_success(self, artist, title, filepath):
        from core.i18n import _
        self.app.update_status(_("status_completed", "Completed: {title}").replace("{title}", title))
        self.app.show_toast(_("status_completed", "Completed: {title}").replace("{title}", title[:20] + "..."), "success")
        self.update_progress(1.0)
        self.app.main_area.btn_cancel.configure(state="disabled")
        
        self.app.main_area.speed_label.configure(text="-")
        self.app.main_area.size_label.configure(text="-")
        
        self.app.url_entry.configure(state="normal")
        self.app.paste_btn.configure(state="normal")
        self.app.download_btn.configure(state="normal")
        self.app.url_entry.delete(0, 'end')
        self.app.right_column.load_history()
        
        # Hide progress and show welcome screen after success
        self.app.after(3000, lambda: self.reset_to_welcome())

    def reset_to_welcome(self):
        self.app.main_area.progress_card.pack_forget()
        self.app.main_area.welcome_frame.pack(fill="both", expand=True, pady=40)

    def update_progress(self, percent, details=None):
        if details and 'item_finished' in details:
            self.app.right_column.load_history()
            return

        if details and details.get('indeterminate'):
            if self.app.main_area.progressbar.cget("mode") != "indeterminate":
                self.app.main_area.progressbar.configure(mode="indeterminate")
                self.app.main_area.progressbar.start()
        else:
            if self.app.main_area.progressbar.cget("mode") == "indeterminate":
                self.app.main_area.progressbar.stop()
                self.app.main_area.progressbar.configure(mode="determinate")
                
            if percent is not None:
                self.app.main_area.progressbar.set(percent)
                self.app.main_area.progress_percent_label.configure(text=f"{int(percent * 100)}%")
                
            if details:
                speed = details.get('speed', '')
                size = details.get('size', '')
                
                if size: self.app.main_area.size_label.configure(text=size)
                if speed: self.app.main_area.speed_label.configure(text=speed)

    def download_music(self, url, output_folder, is_playlist, embed_lrc):
        
        # Колбеки для оновлення GUI з фонового потоку
        def status_cb(msg):
            self.app.after(0, lambda m=msg: self.app.update_status(m))
            
        def progress_cb(percent, details=None):
            self.app.after(0, lambda: self.update_progress(percent, details))
            
        def success_cb(artist, title, filepath):
            self.app.last_downloaded_file = filepath
            self.app.after(0, lambda a=artist, t=title, f=filepath: self.download_success(a, t, f))

        def error_cb(err_msg):
            from core.i18n import _
            safe_msg = str(err_msg).replace("'\n", " ").replace("\n", " | ")
            
            def update_gui_on_error():
                self.app.update_status(_("status_error", "❌ Error: {msg}").replace("{msg}", safe_msg))
                self.app.show_toast(_("status_error_toast", "Download Error"), "error")
                self.app.main_area.prog_track_title.configure(text=_("status_error_title", "ERROR!"), text_color="#E52D27")
                self.app.main_area.prog_track_artist.configure(text=safe_msg[:60] + "..." if len(safe_msg) > 60 else safe_msg)
                
                if self.app.main_area.progressbar.cget("mode") == "indeterminate":
                    self.app.main_area.progressbar.stop()
                self.app.main_area.progressbar.configure(mode="determinate")
                self.app.main_area.progressbar.set(0)
                
                self.app.url_entry.configure(state="normal")
                self.app.paste_btn.configure(state="normal")
                self.app.download_btn.configure(state="normal")
                self.app.main_area.btn_cancel.configure(state="disabled")
                
            self.app.after(0, update_gui_on_error)

        def set_process_cb(p):
            self.current_download_process = p
            
        from core.download_engine import download_and_process_music
        # Передаємо керування в Engine. qual також передається з налаштувань, якщо потрібно.
        qual = self.app.config.get("quality", "320")
        use_sponsorblock = self.app.config.get("use_sponsorblock", True)
        download_and_process_music(url, output_folder, is_playlist, embed_lrc, status_cb, progress_cb, success_cb, error_cb, set_process_cb, qual, use_sponsorblock)
