import customtkinter as ctk
from PIL import Image
import os
import webbrowser
from core.i18n import _

class MainAreaFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        kwargs.setdefault("fg_color", ("#FFFFFF", "#1A1A1A"))
        kwargs.setdefault("corner_radius", 18)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", ("#E5E7EB", "#2A2A2A"))
        super().__init__(master, **kwargs)
        self.app = app
        
        # ====== INPUT CARD ======
        self.input_card = ctk.CTkFrame(self, fg_color="transparent")
        self.input_card.pack(fill="x", pady=(10, 0), padx=10)

        self.input_label = ctk.CTkLabel(self.input_card, text=_("input_label", "YouTube Video or Playlist URL"), font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color=("#111827", "#e5e7eb"))
        self.input_label.pack(anchor="w", padx=25, pady=(25, 10))

        self.input_row = ctk.CTkFrame(self.input_card, fg_color="transparent")
        self.input_row.pack(fill="x", padx=25, pady=(0, 20))

        self.url_entry = ctk.CTkEntry(
            self.input_row, placeholder_text="https://www.youtube.com/watch?v=...", 
            height=42, font=ctk.CTkFont(family="Segoe UI", size=14), border_color=("#D1D5DB", "#333333"), 
            fg_color=("#F9FAFB", "#121212"), border_width=1, corner_radius=8
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.paste_btn = ctk.CTkButton(
            self.input_row, text="📋 " + _("paste", "Paste"), width=100, height=42, corner_radius=8, 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), fg_color=("#F3F4F6", "#2A2A2A"), hover_color=("#E5E7EB", "#3A3A3A"), text_color=("#111827", "#ffffff"),
            command=self.app.paste_from_clipboard
        )
        self.paste_btn.pack(side="left", padx=10)

        self.download_btn = ctk.CTkButton(
            self.input_row, text=_("download", "⬇ Download"), width=120, height=42, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), 
            fg_color="#E52D27", hover_color="#C0201E", command=lambda: self.app.download_controller.start_download_thread(),
            state="disabled"
        )
        self.download_btn.pack(side="right")

        # ====== PREVIEW CARD ======
        self.preview_card = ctk.CTkFrame(self.input_card, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=16, border_width=1, border_color="#E52D27")
        
        self.thumbnail_label = ctk.CTkLabel(self.preview_card, text="", width=120, height=67, fg_color=("#F3F4F6", "#2A2A2A"), corner_radius=8)
        self.thumbnail_label.pack(side="left", padx=(25, 15), pady=25)

        self.info_frame = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.info_frame.pack(side="left", fill="both", expand=True, pady=15)

        self.preview_title = ctk.CTkLabel(self.info_frame, text=_("preview_ready", "Ready to download"), font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color=("#111827", "#ffffff"), anchor="w", justify="left")
        self.preview_title.pack(fill="x")

        self.preview_artist = ctk.CTkLabel(self.info_frame, text=_("preview_paste", "Paste a link above"), font=ctk.CTkFont(family="Segoe UI", size=14), text_color=("#6B7280", "#a1a1aa"), anchor="w")
        self.preview_artist.pack(fill="x", pady=(2, 0))
        
        # Spacer to force CustomTkinter to draw the border to the right edge
        ctk.CTkFrame(self.preview_card, width=1, height=1, fg_color="transparent").pack(side="right")

        # Progress Card
        self.progress_card = ctk.CTkFrame(self.input_card, fg_color=("#FFFFFF", "#1A1A1A"), corner_radius=18, border_width=1, border_color=("#E5E7EB", "#2A2A2A"))
        # Initially hide the progress card to prevent empty UI blocks
        # self.progress_card.pack(fill="x")

        self.prog_title = ctk.CTkLabel(self.progress_card, text=_("prog_title", "Download Progress"), font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=("#111827", "#ffffff"))
        self.prog_title.pack(anchor="w", padx=25, pady=(20, 15))

        self.prog_info_frame = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        self.prog_info_frame.pack(fill="x", padx=25, pady=(0, 15))

        self.prog_thumb = ctk.CTkLabel(self.prog_info_frame, text="", width=120, height=67, fg_color=("#F3F4F6", "#2A2A2A"), corner_radius=8)
        self.prog_thumb.pack(side="left", padx=(0, 15))

        self.prog_text_frame = ctk.CTkFrame(self.prog_info_frame, fg_color="transparent")
        self.prog_text_frame.pack(side="left", fill="both", expand=True)

        self.prog_track_title = ctk.CTkLabel(self.prog_text_frame, text=_("prog_waiting", "Waiting..."), font=ctk.CTkFont(size=14, weight="bold"), text_color=("#374151", "#d1d5db"), anchor="w")
        self.prog_track_title.pack(fill="x")
        self.prog_track_artist = ctk.CTkLabel(self.prog_text_frame, text="-", font=ctk.CTkFont(size=12), text_color=("#6B7280", "#9ca3af"), anchor="w")
        self.prog_track_artist.pack(fill="x")

        self.progress_percent_label = ctk.CTkLabel(self.prog_info_frame, text="0%", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=("#E52D27", "#E52D27"))
        self.progress_percent_label.pack(side="right", padx=(15, 0), anchor="center")

        self.prog_bar_frame = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        self.prog_bar_frame.pack(fill="x", padx=25, pady=(0, 15))

        self.progressbar = ctk.CTkProgressBar(self.prog_bar_frame, height=6, progress_color="#E52D27", fg_color=("#E5E7EB", "#333333"), corner_radius=3)
        self.progressbar.pack(fill="x", pady=(0, 5))
        self.progressbar.set(0)

        self.details_container = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        self.details_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        self.stats_frame = ctk.CTkFrame(self.details_container, fg_color="transparent")
        self.stats_frame.pack(side="left", fill="both", expand=True)
        
        self.status_label = ctk.CTkLabel(self.stats_frame, text=_("status_ready", "Status: Ready"), font=ctk.CTkFont(size=15, weight="bold"), text_color=("#374151", "#d1d5db"), anchor="w")
        self.status_label.pack(anchor="w", pady=(0, 10))
        
        self.metrics_grid = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.metrics_grid.pack(fill="x")
        self.metrics_grid.grid_columnconfigure((0, 1), weight=1)
        self.metrics_grid.grid_columnconfigure(2, weight=0)

        self.size_card = ctk.CTkFrame(self.metrics_grid, fg_color=("#F3F4F6", "#2A2A2A"), corner_radius=10)
        self.size_card.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        lbl_s1 = ctk.CTkLabel(self.size_card, text=_("size", "SIZE"), font=ctk.CTkFont(size=11, weight="bold"), text_color=("#6B7280", "#9ca3af"))
        lbl_s1.pack(anchor="w", padx=10, pady=(8, 0))
        self.size_label = ctk.CTkLabel(self.size_card, text="-", font=ctk.CTkFont(size=16, weight="bold"), text_color=("#111827", "#ffffff"))
        self.size_label.pack(anchor="w", padx=10, pady=(0, 8))

        self.speed_card = ctk.CTkFrame(self.metrics_grid, fg_color=("#F3F4F6", "#2A2A2A"), corner_radius=10)
        self.speed_card.grid(row=0, column=1, sticky="ew", padx=(5, 10))
        lbl_s2 = ctk.CTkLabel(self.speed_card, text=_("speed", "SPEED"), font=ctk.CTkFont(size=11, weight="bold"), text_color=("#6B7280", "#9ca3af"))
        lbl_s2.pack(anchor="w", padx=10, pady=(8, 0))
        self.speed_label = ctk.CTkLabel(self.speed_card, text="-", font=ctk.CTkFont(size=16, weight="bold"), text_color=("#111827", "#ffffff"))
        self.speed_label.pack(anchor="w", padx=10, pady=(0, 8))

        self.btns_frame = ctk.CTkFrame(self.metrics_grid, fg_color="transparent")
        self.btns_frame.grid(row=0, column=2, sticky="se", padx=(15, 0))

        self.btn_cancel = ctk.CTkButton(self.btns_frame, text=_("cancel", "Cancel"), width=100, height=36, fg_color="transparent", border_width=1, border_color="#ef4444", hover_color=("#fee2e2", "#7f1d1d"), text_color="#ef4444", state="disabled")
        self.btn_cancel.pack(side="right", padx=5)
        
        # Spacer to force CustomTkinter to draw the border to the right edge
        ctk.CTkFrame(self.progress_card, width=1, height=1, fg_color="transparent").pack(side="right")

        # ====== WELCOME / EMPTY STATE ======
        self.welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.welcome_frame.pack(fill="both", expand=True, pady=40)
        
        icon_lbl = ctk.CTkLabel(self.welcome_frame, text="🎸", font=ctk.CTkFont(size=64), text_color=("#D1D5DB", "#333333"))
        icon_lbl.pack(pady=(20, 10))
        
        title_lbl = ctk.CTkLabel(self.welcome_frame, text=_("welcome_title", "Ready to Download"), font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=("#374151", "#d1d5db"))
        title_lbl.pack(pady=(0, 5))
        
        hint_lbl = ctk.CTkLabel(self.welcome_frame, text=_("welcome_desc", "Paste a YouTube link above to extract music.\nYour history and queue will appear on the right."), font=ctk.CTkFont(family="Segoe UI", size=14), text_color=("#9CA3AF", "#6b7280"), justify="center")
        hint_lbl.pack()
