import customtkinter as ctk
import auth
import os
from PIL import Image, ImageDraw
import database as db

class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_login):
        super().__init__(master)
        self.on_login = on_login

        # Main backdrop matching the outer image border
        self.configure(fg_color="#7b9e99")
        
        # The central floating container (simulating the web browser card)
        main_card = ctk.CTkFrame(self, corner_radius=25, fg_color="white")
        main_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)
        
        main_card.grid_columnconfigure(0, weight=1, uniform="col")
        main_card.grid_columnconfigure(1, weight=1, uniform="col")
        main_card.grid_rowconfigure(0, weight=1)

        # ---------------- LEFT SIDE ----------------
        left_color = "#b3f4ec"
        left_panel = ctk.CTkFrame(main_card, corner_radius=20, fg_color=left_color)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # Mock badge
        badge = ctk.CTkFrame(left_panel, fg_color="white", corner_radius=5)
        badge.pack(pady=(40, 20))
        ctk.CTkLabel(badge, text="🔹 PERTAMINA", text_color="black", font=("Arial", 12, "bold")).pack(padx=10, pady=5)

        # Pattern Image (Rounded Corners)
        try:
            bg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "desk_pattern.png")
            img = Image.open(bg_path).convert("RGBA")
            
            # Create rounded mask
            mask = Image.new('L', img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=30, fill=255)
            img.putalpha(mask)
            
            bg_image = ctk.CTkImage(img, size=(380, 420)) 
            ctk.CTkLabel(left_panel, image=bg_image, text="").pack(pady=20, expand=True)
        except Exception:
            pass

        # ---------------- RIGHT SIDE ----------------
        right_panel = ctk.CTkFrame(main_card, corner_radius=20, fg_color="white")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        # Center form container relative to the right panel
        form = ctk.CTkFrame(right_panel, fg_color="white")
        form.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8)

        # Logo and Title
        ctk.CTkLabel(form, text="📊 Inventory", font=("Georgia", 42, "bold"), text_color="#5c4f48").pack(pady=(0, 5))
        ctk.CTkLabel(form, text="Login", font=("Arial", 16), text_color="gray").pack(pady=(0, 20))

        # Inputs
        ctk.CTkLabel(form, text="Email / Username", text_color="gray", font=("Arial", 14)).pack(anchor="w")
        self.username_entry = ctk.CTkEntry(form, placeholder_text="✉  Type your username", 
                                           height=45, corner_radius=10, 
                                           border_color="#cccccc", fg_color="white", text_color="black")
        self.username_entry.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(form, text="Password", text_color="gray", font=("Arial", 14)).pack(anchor="w")
        self.password_entry = ctk.CTkEntry(form, placeholder_text="🔒 ••••••••", show="•",
                                           height=45, corner_radius=10, 
                                           border_color="#cccccc", fg_color="white", text_color="black")
        self.password_entry.pack(fill="x", pady=(5, 20))
        self.password_entry.bind("<Return>", lambda e: self._login())

        self.error_label = ctk.CTkLabel(form, text="", text_color="#e74c3c", font=("Arial", 13))
        self.error_label.pack()

        # Login button
        ctk.CTkButton(form, text="Login", font=("Arial", 16, "bold"), fg_color="#36dac5", hover_color="#2eb3a2", 
                      text_color="white", height=45, corner_radius=10, command=self._login).pack(fill="x", pady=(10, 0))

    def _login(self):
        username = self.username_entry.get().strip()
        user = auth.login(username, self.password_entry.get())
        if user:
            db.log_action(username, "LOGIN", "Successful login")
            self.on_login(user)
        else:
            db.log_action(username or "unknown", "LOGIN_FAILED", "Invalid credentials")
            self.error_label.configure(text="Invalid username or password")
