import customtkinter as ctk
from PIL import Image
import os

class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app

        icon_size = (18, 18)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
        
        try:
            self.img_dashboard = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "dashboard_active.png")), size=icon_size)
            self.img_library = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "library.png")), size=icon_size)
            self.img_history = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "history.png")), size=icon_size)
            self.img_play = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "play.png")), size=icon_size)
            self.img_settings = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "settings.png")), size=icon_size)
            self.img_logo = ctk.CTkImage(light_image=Image.open(os.path.join(icon_path, "logo.png")), size=(28, 28))
        except Exception:
            self.img_dashboard = self.img_library = self.img_history = self.img_play = self.img_settings = self.img_logo = None

        self.grid_rowconfigure(5, weight=1) # Spacer

        self.logo_label = ctk.CTkLabel(self, image=self.img_logo, text=" YT Music", font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"), text_color=("#111827", "#ffffff"), compound="left")
        self.logo_label.grid(row=0, column=0, padx=24, pady=(30, 35), sticky="w")

        # Навігаційні кнопки з більшим corner_radius та приємнішими кольорами
        btn_font = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        
        self.btn_dashboard = ctk.CTkButton(self, image=self.img_dashboard, text="  Dashboard", fg_color=("#E5E7EB", "#1A1A1A"), text_color="#E52D27", hover_color=("#D1D5DB", "#2A2A2A"), anchor="w", font=btn_font, width=170, height=45, corner_radius=10, command=self.app.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=5)

        self.btn_library = ctk.CTkButton(self, image=self.img_library, text="  Library", fg_color="transparent", text_color=("#374151", "#d1d5db"), hover_color=("#E5E7EB", "#2A2A2A"), anchor="w", font=ctk.CTkFont(family="Segoe UI", size=15), width=170, height=45, corner_radius=10, command=self.app.show_library)
        self.btn_library.grid(row=2, column=0, padx=20, pady=5)

        self.btn_history = ctk.CTkButton(self, image=self.img_history, text="  History", fg_color="transparent", text_color=("#374151", "#d1d5db"), hover_color=("#E5E7EB", "#2A2A2A"), anchor="w", font=ctk.CTkFont(family="Segoe UI", size=15), width=170, height=45, corner_radius=10, command=self.app.show_history)
        self.btn_history.grid(row=3, column=0, padx=20, pady=5)



        self.btn_settings = ctk.CTkButton(self, image=self.img_settings, text="  Settings", fg_color="transparent", text_color=("#6B7280", "#9ca3af"), hover_color=("#E5E7EB", "#2A2A2A"), anchor="w", font=ctk.CTkFont(family="Segoe UI", size=15), width=170, height=45, corner_radius=10, command=self.app.show_settings)
        self.btn_settings.grid(row=6, column=0, padx=20, pady=(0, 25))
