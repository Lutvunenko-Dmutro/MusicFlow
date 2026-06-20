"""
app_setup.py — побудова UI та прив'язка подій для App (gui_app.py).
"""
import os
import tkinter as tk
import customtkinter as ctk


def setup_ui(app):
    """Створює всі UI-компоненти App."""
    from ui.sidebar import SidebarFrame
    from ui.main_area import MainAreaFrame
    from ui.right_column import RightColumnFrame
    from ui.player_bar import PlayerBarFrame
    from ui.library import LibraryFrame
    from ui.history import HistoryFrame
    from ui.settings import SettingsFrame

    app.grid_rowconfigure(0, weight=1)
    app.grid_rowconfigure(1, weight=0)
    app.grid_columnconfigure(0, weight=0)
    app.grid_columnconfigure(1, weight=1)
    app.grid_columnconfigure(2, weight=0, minsize=320)

    app.output_folder = app.config.get(
        "output_folder",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "My_Music")
    )
    os.makedirs(app.output_folder, exist_ok=True)

    app.sidebar = SidebarFrame(app, app)
    app.sidebar.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)

    app.main_area = MainAreaFrame(app, app)
    app.main_area.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)

    app.right_column = RightColumnFrame(app, app)
    app.right_column.grid(row=0, column=2, sticky="nsew", padx=(10, 20), pady=20)

    app.library_area  = LibraryFrame(app, app)
    app.history_area  = HistoryFrame(app, app)
    app.settings_area = SettingsFrame(app, app)

    app.player_bar = PlayerBarFrame(app, app)
    app.player_bar.grid(row=1, column=0, columnspan=3, sticky="sew")

    # Shortcuts
    app.url_entry    = app.main_area.url_entry
    app.paste_btn    = app.main_area.paste_btn
    app.download_btn = app.main_area.download_btn
    app.progressbar  = app.main_area.progressbar
    app.status_label = app.main_area.status_label
    app.eta_label    = app.main_area.eta_label
    app.speed_label  = app.main_area.speed_label

    # Right-click context menu
    app.context_menu = tk.Menu(app, tearoff=False, bg="#2b2b2b", fg="white",
                               font=("Segoe UI", 11))
    app.context_menu.add_command(label="Вставити", command=app.paste_from_clipboard)
    app.context_menu.add_command(label="Очистити",
                                 command=lambda: app.url_entry.delete(0, 'end'))


def setup_bindings(app):
    """Прив'язує всі клавіатурні та мишкові події."""
    app.url_entry.focus_set()
    app.typing_timer = None
    app.url_entry.bind("<KeyRelease>", app.on_url_typing)
    app.url_entry.bind(
        "<Return>",
        lambda e: app.download_controller.start_download_thread()
        if app.download_btn.cget("state") == "normal" else None
    )
    app.url_entry.bind("<Control-KeyPress>", app.handle_ctrl_v)
    app.url_entry.bind("<Button-3>", app.show_context_menu)
    app.main_area.btn_finish.configure(command=app.reset_ui)
