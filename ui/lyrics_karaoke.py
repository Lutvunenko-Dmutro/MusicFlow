import customtkinter as ctk
import re
import os

class KaraokeLyricsUI:
    def __init__(self, app, lyrics_text, on_regenerate=None):
        self.app = app
        self.dialog = ctk.CTkToplevel(app)
        self.dialog.title("Караоке (Синхронізований текст)")
        self.dialog.geometry("450x600")
        self.dialog.attributes('-topmost', True)
        
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.ico")
            self.dialog.after(200, lambda: self.dialog.iconbitmap(icon_path))
        except Exception:
            pass
        
        
        self.dialog.update_idletasks()
        x = self.app.winfo_x() + (self.app.winfo_width() - 450) // 2
        y = self.app.winfo_y() + (self.app.winfo_height() - 600) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self.lines = []
        self.active_idx = -1
        
        self.scroll = ctk.CTkScrollableFrame(self.dialog, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        if lyrics_text:
            self._parse_and_render_lyrics(lyrics_text)
        else:
            lbl = ctk.CTkLabel(self.scroll, text="Текст пісні ще не згенеровано.", justify="center", font=ctk.CTkFont(size=15, weight="bold"))
            lbl.pack(pady=(50, 20))
            
        btn_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        btn_text = "Перегенерувати текст (AI)" if lyrics_text else "Згенерувати текст (AI)"
        
        if on_regenerate:
            def _on_gen():
                self.dialog.destroy()
                on_regenerate()
                
            btn_gen = ctk.CTkButton(btn_frame, text=btn_text, fg_color="#E52D27", hover_color="#c0241f", command=_on_gen)
            btn_gen.pack(pady=10)
            
    def _parse_and_render_lyrics(self, text):
        raw_lines = text.split('\n')
        for line in raw_lines:
            line = line.strip()
            if not line: continue
            
            # Шукаємо LRC timestamp: [00:15.50]
            match = re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)', line)
            if match:
                m = int(match.group(1))
                s = float(match.group(2))
                time_sec = m * 60 + s
                content = match.group(3)
                self.lines.append({'time': time_sec, 'text': content, 'label': None})
            else:
                self.lines.append({'time': -1, 'text': line, 'label': None})
                
        for item in self.lines:
            lbl = ctk.CTkLabel(self.scroll, text=item['text'], font=ctk.CTkFont(size=16), text_color="#9CA3AF") # Gray
            lbl.pack(pady=4)
            item['label'] = lbl
            
    def sync_lyrics(self, current_time):
        if not self.lines:
            return
            
        # Знаходимо останній рядок, час якого менший або дорівнює поточному
        idx = -1
        for i, item in enumerate(self.lines):
            if item['time'] >= 0 and current_time >= item['time']:
                idx = i
                
        if idx != self.active_idx and idx >= 0:
            # Знімаємо підсвітку з попереднього
            if self.active_idx >= 0 and self.lines[self.active_idx]['label']:
                self.lines[self.active_idx]['label'].configure(font=ctk.CTkFont(size=16), text_color="#9CA3AF")
                
            # Підсвічуємо поточний
            self.active_idx = idx
            if self.lines[self.active_idx]['label']:
                self.lines[self.active_idx]['label'].configure(font=ctk.CTkFont(size=20, weight="bold"), text_color="#FFFFFF")
                
                # Автоскролл
                try:
                    fraction = idx / max(len(self.lines), 1)
                    # Віднімаємо трохи, щоб активний рядок був по центру, а не в самому верху
                    self.scroll._parent_canvas.yview_moveto(max(0.0, fraction - 0.4))
                except Exception:
                    pass
