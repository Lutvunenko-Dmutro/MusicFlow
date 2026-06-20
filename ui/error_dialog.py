import customtkinter as ctk
import os

class ErrorDialog(ctk.CTkToplevel):
    def __init__(self, title_text, error_details, log_path, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Crash Reporter")
        self.geometry("700x450")
        self.attributes("-topmost", True)
        self.log_path = log_path
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        lbl = ctk.CTkLabel(self, text=f"🚨 {title_text}", font=("Segoe UI", 20, "bold"), text_color="#ef4444")
        lbl.pack(pady=(20, 5))
        
        sub_lbl = ctk.CTkLabel(self, text="Програма перехопила неочікувану помилку і залогувала її. Подробиці:", font=("Segoe UI", 13))
        sub_lbl.pack(pady=(0, 10))
        
        textbox = ctk.CTkTextbox(self, width=650, height=260, font=("Consolas", 12))
        textbox.pack(pady=10, padx=20, fill="both", expand=True)
        textbox.insert("0.0", error_details)
        textbox.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        btn_log = ctk.CTkButton(btn_frame, text="Відкрити лог файл", command=self.open_log, width=150)
        btn_log.pack(side="left", padx=10)
        
        btn_close = ctk.CTkButton(btn_frame, text="Закрити", fg_color="#ef4444", hover_color="#dc2626", command=self.destroy, width=150)
        btn_close.pack(side="left", padx=10)
        
        self.focus()

    def open_log(self):
        try:
            if os.name == 'nt':
                os.startfile(self.log_path)
            else:
                import subprocess
                subprocess.call(['xdg-open', self.log_path])
        except Exception as e:
            print(f"Failed to open log: {e}")

def show_error_window(title, error_details, log_path, is_standalone=False):
    if is_standalone:
        # Створюємо ізольоване вікно, якщо головна програма повністю мертва або ще не запустилася
        app = ctk.CTk()
        app.withdraw() # Ховаємо технічне базове вікно
        dialog = ErrorDialog(title, error_details, log_path, master=app)
        
        def on_close():
            dialog.destroy()
            app.destroy()
            
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        # Перевизначаємо кнопку закриття
        for widget in dialog.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for btn in widget.winfo_children():
                    if btn.cget("text") == "Закрити":
                        btn.configure(command=on_close)
        
        app.mainloop()
    else:
        # Використовуємо існуючий event loop головного вікна
        dialog = ErrorDialog(title, error_details, log_path)
        dialog.grab_set() # Блокує взаємодію з основним вікном до закриття помилки
