"""
player_bar_ui.py — побудова UI панелі плеєра.
"""
import os
import customtkinter as ctk
from PIL import Image
from ui.audio_visualizer import AudioVisualizer

def load_icon(icons_dir, name, size):
    path = os.path.join(icons_dir, name)
    if os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    return None


def load_icon_simple(path, size):
    if os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    return None


def build_player_bar(bar):
    """
    Будує всі UI-елементи PlayerBarFrame (bar).
    Присвоює атрибути безпосередньо до об'єкта bar.
    """
    icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")

    bar.icon_play  = load_icon(icons_dir, "play.png",  22)
    bar.icon_pause = load_icon(icons_dir, "pause.png", 22)
    bar.icon_next  = load_icon(icons_dir, "next.png",  20)
    bar.icon_prev  = load_icon(icons_dir, "prev.png",  20)
    bar.icon_stop  = load_icon(icons_dir, "stop.png",  18)

    bar.icon_shuffle        = load_icon_simple(os.path.join(icons_dir, "shuffle.png"),          (20, 20))
    bar.icon_shuffle_act    = load_icon_simple(os.path.join(icons_dir, "shuffle_active.png"),   (20, 20))
    bar.icon_repeat         = load_icon_simple(os.path.join(icons_dir, "repeat.png"),           (20, 20))
    bar.icon_repeat_act     = load_icon_simple(os.path.join(icons_dir, "repeat_active.png"),    (20, 20))
    bar.icon_repeat_one     = load_icon_simple(os.path.join(icons_dir, "repeat_one.png"),       (20, 20))
    bar.icon_repeat_one_act = load_icon_simple(os.path.join(icons_dir, "repeat_one_active.png"),(20, 20))

    bar.grid_columnconfigure(0, weight=1)
    bar.grid_columnconfigure(1, weight=0)
    bar.grid_columnconfigure(2, weight=1)

    sep = ctk.CTkFrame(bar, fg_color=("#E5E7EB", "#2a2a2a"), height=1)
    sep.place(x=0, y=0, relwidth=1)

    _build_left_panel(bar, icons_dir)
    _build_center_panel(bar)
    _build_right_panel(bar)

    bar.bind("<Configure>", bar.on_resize)
    bar.update_progress_loop()


def _build_left_panel(bar, icons_dir):
    bar.info_frame = ctk.CTkFrame(bar, fg_color="transparent")
    bar.info_frame.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=12)

    placeholder_path = os.path.join(icons_dir, "music_placeholder.png")
    bar.default_cover = Image.open(placeholder_path) if os.path.exists(placeholder_path) else None

    bar.cover_lbl = ctk.CTkLabel(
        bar.info_frame, text="♪", width=56, height=56,
        fg_color=("#E5E7EB", "#222222"), corner_radius=8,
        font=ctk.CTkFont(size=22), text_color=("#9CA3AF", "#555555")
    )
    bar.cover_lbl.pack(side="left", padx=(0, 15))

    bar.text_frame = ctk.CTkFrame(bar.info_frame, fg_color="transparent")
    bar.text_frame.pack(side="left")

    from core.i18n import _
    bar.title_lbl = ctk.CTkLabel(
        bar.text_frame, text=_("no_track", "No track selected"),
        font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        text_color=("#111827", "#f1f5f9"), anchor="w", width=160
    )
    bar.title_lbl.pack(anchor="w")

    bar.artist_lbl = ctk.CTkLabel(
        bar.text_frame, text="-",
        font=ctk.CTkFont(family="Segoe UI", size=13),
        text_color=("#6B7280", "#6b7280"), anchor="w", width=160
    )
    bar.artist_lbl.pack(anchor="w", pady=(2, 0))

    bar.visualizer_frame = ctk.CTkFrame(bar.info_frame, fg_color="transparent")
    bar.visualizer_frame.pack(side="left", padx=(18, 0))
    bar.visualizer = AudioVisualizer(bar.visualizer_frame, app=bar.app, width=240, height=48, bars=60)
    bar.visualizer.pack()


def _build_center_panel(bar):
    bar.center_frame = ctk.CTkFrame(bar, fg_color="transparent")
    bar.center_frame.grid(row=1, column=1, pady=12)

    bar.controls_frame = ctk.CTkFrame(bar.center_frame, fg_color="transparent")
    bar.controls_frame.pack(pady=(12, 5))

    btn_cfg = dict(text="", fg_color="transparent", hover_color=("#E5E7EB", "#1e1e1e"), corner_radius=20)

    for attr, icon_attr, cmd, w, padx in [
        ("btn_shuffle",    "icon_shuffle", bar.toggle_shuffle,                      40, (0, 4)),
        ("btn_prev",       "icon_prev",    lambda: bar.app.play_prev_song(),         40, (0, 8)),
    ]:
        btn = ctk.CTkButton(bar.controls_frame, image=getattr(bar, icon_attr),
                            width=w, height=40, command=cmd, **btn_cfg)
        btn.pack(side="left", padx=padx)
        setattr(bar, attr, btn)

    bar.btn_play_pause = ctk.CTkButton(
        bar.controls_frame, text="", image=bar.icon_play,
        width=50, height=50, corner_radius=25,
        fg_color="#E52D27", hover_color="#c0241f",
        command=bar.toggle_play
    )
    bar.btn_play_pause.pack(side="left", padx=10)

    for attr, icon_attr, cmd, padx in [
        ("btn_next", "icon_next", lambda: bar.app.play_next_song(), (8, 0)),
        ("btn_stop", "icon_stop", bar.stop_music,                   (8, 4)),
        ("btn_repeat", "icon_repeat", bar.toggle_repeat,            (0, 0)),
    ]:
        btn = ctk.CTkButton(bar.controls_frame, image=getattr(bar, icon_attr),
                            width=40, height=40, command=cmd, **btn_cfg)
        btn.pack(side="left", padx=padx)
        setattr(bar, attr, btn)

    bar.progress_frame = ctk.CTkFrame(bar.center_frame, fg_color="transparent")
    bar.progress_frame.pack(fill="x", padx=40)

    bar.time_current_lbl = ctk.CTkLabel(
        bar.progress_frame, text="0:00",
        font=ctk.CTkFont(size=12), text_color=("#6B7280", "#6b7280"), width=35
    )
    bar.time_current_lbl.pack(side="left", padx=10)

    bar.progress_slider = ctk.CTkSlider(
        bar.progress_frame, from_=0, to=100, command=bar.seek,
        button_color=("#111827", "#ffffff"), button_hover_color=("#374151", "#f9fafb"),
        fg_color=("#D1D5DB", "#333333"), progress_color="#E52D27", height=12
    )
    bar.progress_slider.bind("<ButtonPress-1>",   lambda e: setattr(bar, "is_seeking", True))
    bar.progress_slider.bind("<ButtonRelease-1>", lambda e: bar.perform_seek(bar.progress_slider.get()))
    bar.progress_slider.set(0)
    bar.progress_slider.pack(side="left", padx=8)

    bar.time_total_lbl = ctk.CTkLabel(
        bar.progress_frame, text="0:00",
        font=ctk.CTkFont(size=12), text_color=("#6B7280", "#6b7280"), width=35
    )
    bar.time_total_lbl.pack(side="right", padx=10)


def _build_right_panel(bar):
    bar.right_frame = ctk.CTkFrame(bar, fg_color="transparent")
    bar.right_frame.grid(row=1, column=2, sticky="e", padx=(10, 24), pady=12)

    bar.mini_lyrics_lbl = ctk.CTkLabel(
        bar.right_frame, text=" ",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color="#FCA5A5", width=250, anchor="e",
        wraplength=250, justify="right"
    )
    bar.mini_lyrics_lbl.pack(side="left", padx=(0, 20))

    bar.btn_lyrics = ctk.CTkButton(
        bar.right_frame, text="💬", width=30, height=30,
        fg_color="transparent", hover_color=("#E5E7EB", "#1e1e1e"),
        font=ctk.CTkFont(size=16), text_color=("#6B7280", "#6b7280"),
        command=bar.show_lyrics
    )
    bar.btn_lyrics.pack(side="left", padx=(0, 10))

    bar.vol_icon_lbl = ctk.CTkLabel(
        bar.right_frame, text="🔉",
        font=ctk.CTkFont(size=16), text_color=("#6B7280", "#6b7280")
    )
    bar.vol_icon_lbl.pack(side="left", padx=(0, 5))

    bar.volume_slider = ctk.CTkSlider(
        bar.right_frame, from_=0, to=1, width=100, height=14,
        button_color=("#6B7280", "#9ca3af"), button_hover_color=("#374151", "#f3f4f6"),
        fg_color=("#D1D5DB", "#2a2a2a"), progress_color="#E52D27",
        command=bar.set_volume
    )
    bar.volume_slider.set(0.5)
    bar.volume_slider.pack(side="left")
    bar.engine.set_volume(0.5)


