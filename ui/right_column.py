import customtkinter as ctk
import os

class RightColumnFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        # ====== DOWNLOAD OPTIONS ======
        self.options_card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        self.options_card.pack(fill="x", pady=(0, 20))

        self.options_title = ctk.CTkLabel(self.options_card, text="Download Options", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color=("#111827", "#ffffff"))
        self.options_title.pack(anchor="w", padx=20, pady=(20, 15))

        self.mode_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.mode_frame.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(self.mode_frame, text="Mode:", font=ctk.CTkFont(size=13), text_color=("#6B7280", "#9ca3af"), width=80, anchor="w").pack(side="left")
        self.mode_dropdown = ctk.CTkOptionMenu(self.mode_frame, values=["Single Track", "Full Playlist"], fg_color=("#F9FAFB", "#121212"), button_color=("#E5E7EB", "#333333"), button_hover_color=("#D1D5DB", "#4b5563"), text_color=("#111827", "#ffffff"))
        self.mode_dropdown.pack(side="left", fill="x", expand=True)

        self.format_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.format_frame.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(self.format_frame, text="Format:", font=ctk.CTkFont(size=13), text_color=("#6B7280", "#9ca3af"), width=80, anchor="w").pack(side="left")
        self.format_dropdown = ctk.CTkOptionMenu(self.format_frame, values=["MP3"], fg_color=("#F9FAFB", "#121212"), button_color=("#E5E7EB", "#333333"), button_hover_color=("#D1D5DB", "#4b5563"), text_color=("#111827", "#ffffff"))
        self.format_dropdown.pack(side="right", fill="x", expand=True)

        self.lyrics_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.lyrics_frame.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(self.lyrics_frame, text="Lyrics:", font=ctk.CTkFont(size=13), text_color=("#6B7280", "#9ca3af"), width=80, anchor="w").pack(side="left")
        
        self.lyrics_switch = ctk.CTkSwitch(self.lyrics_frame, text="", progress_color="#E52D27", width=50)
        self.lyrics_switch.select()
        self.lyrics_switch.pack(side="left")

        # ====== RECENT DOWNLOADS CARD ======
        self.history_card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        self.history_card.pack(fill="both", expand=True)

        self.history_title = ctk.CTkLabel(self.history_card, text="Queue / History", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color=("#111827", "#ffffff"))
        self.history_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.history_scroll = ctk.CTkScrollableFrame(self.history_card, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.load_history()

    def choose_folder(self):
        folder = ctk.filedialog.askdirectory(initialdir=self.app.output_folder)
        if folder:
            self.app.output_folder = folder
            self.load_history()

    def load_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        from core.history_manager import get_history_items
        placeholder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "music_placeholder.png")
        items = get_history_items(self.app.output_folder, 50, placeholder_path)
        
        if not items:
            empty_frame = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=40)
            
            icon_lbl = ctk.CTkLabel(empty_frame, text="🎵", font=ctk.CTkFont(size=42), text_color=("#D1D5DB", "#333333"))
            icon_lbl.pack(pady=(0, 10))
            
            title_lbl = ctk.CTkLabel(empty_frame, text="No downloads yet", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color=("#6B7280", "#9ca3af"))
            title_lbl.pack(pady=(0, 5))
            
            hint_lbl = ctk.CTkLabel(empty_frame, text="Paste a YouTube link and\nclick Download to start", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=("#9CA3AF", "#6b7280"))
            hint_lbl.pack()
            return
            
        for item in items:
            item_frame = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            item_frame.pack(fill="x", pady=5)
            
            if item['cover_img']:
                photo = ctk.CTkImage(light_image=item['cover_img'], dark_image=item['cover_img'], size=(36, 36))
                thumb_lbl = ctk.CTkLabel(item_frame, image=photo, text="", fg_color=("#F9FAFB", "#121212"), corner_radius=6)
                thumb_lbl.pack(side="left", padx=(0, 10))

            del_btn = ctk.CTkButton(item_frame, text="🗑", width=25, height=30, fg_color="transparent", hover_color=("#FCA5A5", "#5a1818"), text_color="#ef4444", font=ctk.CTkFont(size=14), command=lambda p=item['path'], fn=item['filename']: self.confirm_delete(p, fn))
            del_btn.pack(side="right", padx=(5, 15))

            play_btn = ctk.CTkButton(item_frame, text="▶", width=30, height=30, fg_color="transparent", hover_color=("#E5E7EB", "#333333"), text_color="#10b981", command=lambda p=item['path']: self.app.play_specific_music(p))
            play_btn.pack(side="right", padx=(5, 0))

            info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True)
            
            display_name = item['filename']
            if len(display_name) > 28: display_name = display_name[:25] + "..."
            name_lbl = ctk.CTkLabel(info_frame, text=display_name, font=ctk.CTkFont(size=12, weight="bold"), text_color=("#374151", "#d1d5db"), anchor="w", justify="left")
            name_lbl.pack(fill="x")
            size_lbl = ctk.CTkLabel(info_frame, text=f"{item['size_mb']:.1f} MB", font=ctk.CTkFont(size=11), text_color=("#9CA3AF", "#6b7280"), anchor="w")
            size_lbl.pack(anchor="w")

    def confirm_delete(self, path, filename):
        # Create a simple confirmation dialog
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Confirm Deletion")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.app)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.app.winfo_x() + (self.app.winfo_width() - 400) // 2
        y = self.app.winfo_y() + (self.app.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")
        
        lbl = ctk.CTkLabel(dialog, text=f"Are you sure you want to delete:\n{filename}?", font=ctk.CTkFont(size=14))
        lbl.pack(pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", fg_color=("#D1D5DB", "#333333"), hover_color=("#9CA3AF", "#4b5563"), text_color=("#111827", "#ffffff"), command=dialog.destroy)
        cancel_btn.pack(side="left", expand=True, padx=5)
        
        def on_confirm():
            dialog.destroy()
            self.delete_music(path)
            
        confirm_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#E52D27", hover_color="#B31217", command=on_confirm)
        confirm_btn.pack(side="right", expand=True, padx=20)

    def delete_music(self, path):
        try:
            # Нормалізуємо шляхи для порівняння (Windows не чутливий до регістру)
            current_path = self.app.player_bar.current_song_path
            if current_path and os.path.normcase(os.path.abspath(current_path)) == os.path.normcase(os.path.abspath(path)):
                self.app.player_bar.stop()
                try:
                    import pygame
                    pygame.mixer.music.unload()
                except AttributeError:
                    pass
                self.app.player_bar.current_song_path = None
                
                # Use after to give OS time to release file lock without blocking GUI
                self.app.after(150, lambda: self._perform_delete(path))
                return
                
            self._perform_delete(path)
        except Exception as e:
            self.app.update_status(f"Помилка видалення: {e}")
            
    def _perform_delete(self, path):
        try:
            from core.history_manager import delete_history_files
            delete_history_files(path)
            self.load_history()
        except Exception as e:
            self.app.update_status(f"Помилка видалення: {e}")

    def on_mode_change(self, choice):
        url = self.app.url_entry.get().strip()
        if url:
            self.app.main_area.preview_title.configure(text="Fetching info...")
            self.app.main_area.preview_artist.configure(text="")
            import threading
            threading.Thread(target=self.app.fetch_preview_info, args=(url,), daemon=True).start()
