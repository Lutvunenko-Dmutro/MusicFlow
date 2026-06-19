import customtkinter as ctk
import os
from PIL import Image

class LibraryFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=("#F3F4F6", "#121212"), **kwargs)
        self.app = app

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(30, 20))

        self.title_label = ctk.CTkLabel(self.header_frame, text="Your Library", font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"), text_color=("#111827", "#ffffff"))
        self.title_label.pack(side="left")

        self.refresh_btn = ctk.CTkButton(self.header_frame, text="🔄 Refresh", width=100, height=35, corner_radius=8, fg_color=("#E5E7EB", "#1E1E1E"), hover_color=("#D1D5DB", "#2A2A2A"), text_color=("#374151", "#ffffff"), font=ctk.CTkFont(family="Segoe UI", size=14), command=self.load_library)
        self.refresh_btn.pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def load_library(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        from core.history_manager import get_history_items
        placeholder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "music_placeholder.png")
        
        items = get_history_items(self.app.output_folder, 1000, placeholder_path)
        
        if not items:
            ctk.CTkLabel(self.scroll_frame, text="Your library is empty. Download some music first!", font=ctk.CTkFont(family="Segoe UI", size=16), text_color=("#6B7280", "#9ca3af")).pack(pady=50)
            return

        for item in items:
            card = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=12, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
            card.pack(fill="x", padx=30, pady=8)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=20, pady=15)

            if item['cover_img']:
                photo = ctk.CTkImage(light_image=item['cover_img'], dark_image=item['cover_img'], size=(50, 50))
                thumb_lbl = ctk.CTkLabel(info_frame, image=photo, text="", fg_color=("#F9FAFB", "#121212"), corner_radius=8)
                thumb_lbl.pack(side="left", padx=(0, 15))

            text_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)

            display_name = item['filename']
            if len(display_name) > 60: display_name = display_name[:57] + "..."
            name_lbl = ctk.CTkLabel(text_frame, text=display_name, font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color=("#111827", "#ffffff"), anchor="w", justify="left")
            name_lbl.pack(fill="x")
            
            size_lbl = ctk.CTkLabel(text_frame, text=f"{item['size_mb']:.1f} MB", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=("#6B7280", "#a1a1aa"), anchor="w")
            size_lbl.pack(anchor="w")

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=15, pady=10)

            play_btn = ctk.CTkButton(btn_frame, text="▶ Play", width=80, height=35, corner_radius=8, fg_color="#E52D27", hover_color="#C0201E", text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), command=lambda p=item['path']: self.app.play_specific_music(p))
            play_btn.pack(side="left", padx=5)

            del_btn = ctk.CTkButton(btn_frame, text="🗑", width=35, height=35, corner_radius=8, fg_color=("#D1D5DB", "#2A2A2A"), hover_color=("#FCA5A5", "#5a1818"), text_color="#ef4444", font=ctk.CTkFont(size=16), command=lambda p=item['path'], fn=item['filename']: self.confirm_delete(p, fn))
            del_btn.pack(side="left", padx=5)

    def confirm_delete(self, path, filename):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Confirm Deletion")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.app)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.app.winfo_x() + (self.app.winfo_width() - 400) // 2
        y = self.app.winfo_y() + (self.app.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")
        
        lbl = ctk.CTkLabel(dialog, text=f"Are you sure you want to delete:\n{filename}?", font=ctk.CTkFont(family="Segoe UI", size=14))
        lbl.pack(pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", fg_color=("#D1D5DB", "#333333"), hover_color=("#9CA3AF", "#4b5563"), text_color=("#111827", "#ffffff"), command=dialog.destroy)
        cancel_btn.pack(side="left", expand=True, padx=20)
        
        def on_confirm():
            dialog.destroy()
            self.delete_music(path)
            
        confirm_btn = ctk.CTkButton(btn_frame, text="Delete", fg_color="#E52D27", hover_color="#B31217", command=on_confirm)
        confirm_btn.pack(side="right", expand=True, padx=20)

    def delete_music(self, path):
        try:
            current_path = self.app.player_bar.current_song_path
            if current_path and os.path.normcase(os.path.abspath(current_path)) == os.path.normcase(os.path.abspath(path)):
                self.app.player_bar.stop()
                try:
                    import pygame
                    pygame.mixer.music.unload()
                except AttributeError:
                    pass
                self.app.player_bar.current_song_path = None
                self.app.after(150, lambda: self._perform_delete(path))
                return
            self._perform_delete(path)
        except Exception as e:
            pass
            
    def _perform_delete(self, path):
        try:
            from core.history_manager import delete_history_files
            delete_history_files(path)
            self.load_library()
            if hasattr(self.app, 'right_column'):
                self.app.right_column.load_history()
        except Exception:
            pass
