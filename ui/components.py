import customtkinter as ctk

class ToastNotification:
    """
    Singleton class to manage toast notifications.
    Displays a floating card with a message that auto-hides.
    """
    _current_toast = None
    _timer_id = None

    @classmethod
    def show(cls, master, message, toast_type="info", duration=3000):
        # Destroy existing toast to avoid stacking
        if cls._current_toast is not None:
            cls._current_toast.destroy()
            if cls._timer_id is not None:
                master.after_cancel(cls._timer_id)

        # Theme based on type
        if toast_type == "error":
            border_color = "#ef4444"
            icon = "❌"
        elif toast_type == "success":
            border_color = "#10b981"
            icon = "✅"
        else:
            border_color = "#3b82f6"
            icon = "ℹ️"

        # Create toast frame
        cls._current_toast = ctk.CTkFrame(
            master, 
            fg_color=("#FFFFFF", "#2A2A2A"),
            border_width=1,
            border_color=border_color,
            corner_radius=8
        )
        
        # We need a small colored line or just a border. A border is nice.
        # Create label
        lbl = ctk.CTkLabel(
            cls._current_toast, 
            text=f"{icon}  {message}", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#111827", "#E0E0E0")
        )
        lbl.pack(padx=20, pady=12)

        # Place at bottom center, slightly above the player bar
        cls._current_toast.place(relx=0.5, rely=0.85, anchor="s")

        def hide_toast():
            if cls._current_toast:
                cls._current_toast.destroy()
                cls._current_toast = None

        cls._timer_id = master.after(duration, hide_toast)
