import customtkinter as ctk
from tkinter import ttk, messagebox
from ui.theme_helper import apply_table_theme

class ImportPreviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, items, new_categories, on_confirm):
        super().__init__(parent)
        self.title("📥 Import Preview")
        self.geometry("1100x700")
        self.items = items
        self.on_confirm = on_confirm
        
        # Make it modal
        self.grab_set()
        self.focus_get()
        
        # Center the window
        self.after(10, self._center_window)
        
        # Main container
        self.container = ctk.CTkFrame(self, fg_color=("white", "gray15"), corner_radius=0)
        self.container.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(self.container, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 20))
        
        ctk.CTkLabel(header, text="Ready to Import?", font=("Arial", 28, "bold"), 
                     text_color=("#111827", "#f9fafb")).pack(side="left")
        
        # Summary Banner
        new_cnt = sum(1 for x in items if not x['exists'])
        upd_cnt = sum(1 for x in items if x['exists'])
        
        summary_frame = ctk.CTkFrame(self.container, fg_color=("#f3f4f6", "gray20"), height=80, corner_radius=15)
        summary_frame.pack(fill="x", padx=40, pady=10)
        summary_frame.pack_propagate(False)

        stats_text = f"📊 Total Items: {len(items)}  |  ✨ New: {new_cnt}  |  🔄 Updates: {upd_cnt}  |  📁 New Categories: {len(new_categories)}"
        ctk.CTkLabel(summary_frame, text=stats_text, font=("Arial", 16, "bold"), 
                     text_color=("#4b5563", "#d1d5db")).pack(expand=True)

        # Table Section
        table_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=40, pady=20)

        apply_table_theme()

        cols = ("name", "category", "size", "price", "stock", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Preview.Treeview")
        
        # Define Headings
        headings = ["Product Name", "Category", "Size", "Price", "Qty", "Status"]
        widths = [350, 150, 100, 100, 80, 120]
        
        for c, h, w in zip(cols, headings, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center" if c != "name" else "w")

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Insert Data
        for item in self.items:
            status = "✨ New Product" if not item['exists'] else "🔄 Update Stock"
            self.tree.insert("", "end", values=(
                item['name'], 
                item['category'], 
                item['size'], 
                f"${item['price']:.2f}", 
                item['stock'],
                status
            ))

        # Bottom Actions
        footer = ctk.CTkFrame(self.container, fg_color="transparent")
        footer.pack(fill="x", padx=40, pady=(10, 40))

        if new_categories:
            cat_list = ", ".join(new_categories[:5]) + ("..." if len(new_categories) > 5 else "")
            ctk.CTkLabel(footer, text=f"⚠️ Will create categories: {cat_list}", 
                         font=("Arial", 13), text_color="#f59e0b").pack(side="left")

        ctk.CTkButton(footer, text="Confirm Import", font=("Arial", 15, "bold"), 
                       fg_color="#36dac5", hover_color="#2eb3a2", width=200, height=45,
                       command=self._confirm).pack(side="right", padx=(15, 0))

        ctk.CTkButton(footer, text="Cancel", font=("Arial", 15), 
                       fg_color="transparent", border_width=1, border_color=("#d1d5db", "gray40"),
                       text_color=("#4b5563", "#d1d5db"), width=120, height=45,
                       command=self.destroy).pack(side="right")

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

    def _confirm(self):
        self.destroy()
        self.on_confirm()
