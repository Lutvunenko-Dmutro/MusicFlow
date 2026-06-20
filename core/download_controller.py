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
        mode = self.app.right_column.mode_dropdown.get()
        fmt = "mp3" # Формат завжди mp3 в цьому UI
        qual = self.app.config.get("quality", "320")
        embed_lrc = self.app.right_column.lyrics_switch.get()

        if not url:
            self.app.update_status("Введіть посилання!")
            return

        # Setup progress preview
        self.app.main_area.welcome_frame.pack_forget()
        self.app.main_area.preview_card.pack_forget()
        self.app.main_area.progress_card.pack(fill="x")
        
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
        self.app.main_area.size_label.configure(text="-")
        self.app.main_area.eta_label.configure(text="-")
        self.app.update_status("✨ Status: Starting...")

        # Setup Cancel button
        self.is_download_cancelled = False
        self.app.main_area.btn_cancel.configure(state="normal", text_color="#ef4444", command=self.cancel_download)

        # Run download in a separate thread so GUI doesn't freeze
        thread = threading.Thread(target=self.download_music, args=(url, self.app.output_folder, mode, embed_lrc))
        thread.start()

    def cancel_download(self):
        self.is_download_cancelled = True
        self.app.main_area.btn_cancel.configure(state="disabled")
        self.app.update_status("Cancelling...")
        
        if self.current_download_process:
            import subprocess
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_download_process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.current_download_process.terminate()
            except Exception:
                pass

    def download_success(self, artist, title, filepath):
        self.app.update_status(f"Completed: {title}")
        self.app.show_toast(f"Download Complete: {title[:20]}...", "success")
        self.update_progress(1.0)
        self.app.main_area.btn_finish.configure(state="normal", text_color="#121212")
        self.app.main_area.btn_cancel.configure(state="disabled")
        
        self.app.main_area.eta_label.configure(text="-")
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
                
            if details:
                
                speed = details.get('speed', '')
                eta = details.get('eta', '')
                size = details.get('size', '')
                
                if size: self.app.main_area.size_label.configure(text=size)
                if speed: self.app.main_area.speed_label.configure(text=speed)
                if eta:
                    if eta == "00:00":
                        self.app.main_area.eta_label.configure(text="00:00")
                    else:
                        self.app.main_area.eta_label.configure(text=eta)

    def download_music(self, url, output_folder, mode, fetch_lyrics):
        
        # Колбеки для оновлення GUI з фонового потоку
        def status_cb(msg):
            self.app.after(0, lambda m=msg: self.app.update_status(m))
            
        def progress_cb(percent, details=None):
            self.app.after(0, lambda: self.update_progress(percent, details))
            
        def success_cb(artist, title, filepath):
            self.app.last_downloaded_file = filepath
            self.app.after(0, lambda a=artist, t=title, f=filepath: self.download_success(a, t, f))

        def error_cb(err_msg):
            safe_msg = str(err_msg).replace("'\n", " ").replace("\n", " | ")
            self.app.after(0, lambda m=safe_msg: self.app.update_status(f"❌ Error: {m}"))
            self.app.after(0, lambda m=safe_msg: self.app.show_toast(f"Download Error", "error"))
            self.app.after(0, lambda m=safe_msg: self.app.main_area.prog_track_title.configure(text="ПОМИЛКА!", text_color="#E52D27"))
            self.app.after(0, lambda m=safe_msg: self.app.main_area.prog_track_artist.configure(text=m[:60] + "..." if len(m) > 60 else m))
            self.app.after(0, lambda: self.app.main_area.progressbar.stop() if self.app.main_area.progressbar.cget("mode") == "indeterminate" else None)
            self.app.after(0, lambda: self.app.main_area.progressbar.configure(mode="determinate"))
            self.app.after(0, lambda: self.app.main_area.progressbar.set(0))
            
            self.app.after(0, lambda: self.app.url_entry.configure(state="normal"))
            self.app.after(0, lambda: self.app.paste_btn.configure(state="normal"))
            self.app.after(0, lambda: self.app.download_btn.configure(state="normal"))
            self.app.after(0, lambda: self.app.main_area.btn_cancel.configure(state="disabled"))

        def set_process_cb(p):
            self.current_download_process = p
            
        from core.download_engine import download_and_process_music
        # Передаємо керування в Engine. qual також передається з налаштувань, якщо потрібно.
        qual = self.app.config.get("quality", "320")
        use_sponsorblock = self.app.config.get("use_sponsorblock", True)
        download_and_process_music(url, output_folder, mode, fetch_lyrics, status_cb, progress_cb, success_cb, error_cb, set_process_cb, qual, use_sponsorblock)
