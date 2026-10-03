"""Theme helper to ensure ttk.Treeview tables properly respond to Light/Dark mode."""
from tkinter import ttk
import customtkinter as ctk


def apply_table_theme(mode=None):
    """
    Applies consistent Light or Dark styling to all ttk.Treeview tables.
    Switches to the 'clam' ttk theme because the Windows native 'vista' theme
    ignores custom background, fieldbackground, and heading colors.
    """
    if mode is None:
        mode = ctk.get_appearance_mode()
    elif mode in ["Light", "Dark"]:
        ctk.set_appearance_mode(mode)
    else:  # "System"
        ctk.set_appearance_mode("system")
        mode = ctk.get_appearance_mode()

    is_dark = (mode == "Dark") or (ctk.get_appearance_mode() == "Dark")

    style = ttk.Style()

    # 'clam' theme allows overriding background & foreground colors on Windows
    try:
        if style.theme_use() != "clam" and "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    if is_dark:
        bg = "#242424"          # Dark table rows
        fg = "#f3f4f6"          # White text
        field_bg = "#242424"    # Background for empty rows
        heading_bg = "#1f2937"  # Dark header background
        heading_fg = "#ffffff"  # White header text
        heading_active = "#374151"
        selected_bg = "#0d9488" # Teal selection
        selected_fg = "#ffffff"
    else:
        bg = "#ffffff"          # White table rows
        fg = "#111827"          # Dark text
        field_bg = "#ffffff"    # Background for empty rows
        heading_bg = "#f3f4f6"  # Soft light header
        heading_fg = "#1f2937"  # Dark header text
        heading_active = "#e5e7eb"
        selected_bg = "#36dac5" # Cyan/teal selection
        selected_fg = "#ffffff"

    # Configure Treeview rows
    for prefix in ["Treeview", "Preview.Treeview"]:
        style.configure(
            prefix,
            background=bg,
            foreground=fg,
            fieldbackground=field_bg,
            borderwidth=0,
            darkcolor=bg,
            lightcolor=bg,
            rowheight=38,
            font=("Arial", 13)
        )
        style.map(
            prefix,
            background=[("selected", selected_bg)],
            foreground=[("selected", selected_fg)]
        )

    # Configure Treeview headers
    for h_prefix in ["Treeview.Heading", "Preview.Treeview.Heading"]:
        style.configure(
            h_prefix,
            background=heading_bg,
            foreground=heading_fg,
            relief="flat",
            borderwidth=0,
            font=("Arial", 13, "bold")
        )
        style.map(
            h_prefix,
            background=[("active", heading_active)],
            foreground=[("active", heading_fg)]
        )
