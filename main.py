#!/usr/bin/env python3
"""Cloth & Jewelry Shop — Inventory Management System"""
import sys
import subprocess
import os

# --- Auto-Installer ---
def check_dependencies():
    try:
        import customtkinter
        import reportlab
    except ImportError:
        print("First-time setup: Missing dependencies found.")
        print("Installing required packages... This may take a minute.")
        try:
            req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
            print("Dependencies installed successfully!")
        except Exception as e:
            print(f"Failed to auto-install dependencies: {e}")
            print("Please run manually: pip install -r requirements.txt")
            sys.exit(1)

check_dependencies()
# ----------------------

import customtkinter as ctk
import database as db
import auth
from ui.login_screen import LoginScreen
from ui.admin_dashboard import AdminDashboard
from ui.cashier_view import CashierView
from ui.theme_helper import apply_table_theme


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Inventory Manager")
        self.geometry("1100x700")
        self.minsize(960, 620)
        self.after(200, lambda: self.state('zoomed')) # Maximized window
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        apply_table_theme("Light")

        db.init_db()
        auth.seed_god_user()
        auth.seed_default_admin()

        self.current_frame = None
        self._show_login()

    def _clear(self):
        if self.current_frame:
            self.current_frame.destroy()

    def _show_login(self):
        self._clear()
        self.current_frame = LoginScreen(self, self._on_login)
        self.current_frame.pack(fill="both", expand=True)

    def _on_login(self, user):
        self._clear()
        if user["role"] in ("admin", "god"):
            self.current_frame = AdminDashboard(self, user, self._show_login)
        else:
            self.current_frame = CashierView(self, user, self._show_login)
        self.current_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    App().mainloop()
