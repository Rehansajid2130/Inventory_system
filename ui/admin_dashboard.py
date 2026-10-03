import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import database as db
import inventory as inv
import auth
from ui.import_preview import ImportPreviewDialog
from ui.theme_helper import apply_table_theme


class AdminDashboard(ctk.CTkFrame):
    def __init__(self, master, user, on_logout):
        super().__init__(master)
        self.user = user
        self.on_logout = on_logout
        self.sort_by = "date_added"
        self.sort_dir = "DESC"
        self.configure(fg_color=("#f4f7f6", "gray10"))
        self._build_sidebar()
        self._build_content()
        self._show_inventory()

    # ---- sidebar ----
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=220, corner_radius=20, fg_color=("white", "gray15"), border_width=1, border_color=("#e5e7eb", "gray30"))
        sb.pack(side="left", fill="y", padx=15, pady=15)
        sb.pack_propagate(False)

        ctk.CTkLabel(sb, text="📦 Inventory\nAdmin", font=("", 22, "bold")).pack(pady=(24, 4))
        role_label = "Admin" if self.user["role"] == "admin" else "God Mode"
        ctk.CTkLabel(sb, text=f"Logged in as {self.user['username']} ({role_label})", font=("", 13), text_color="gray", wraplength=180).pack(pady=(0, 20))

        buttons = [
            ("📊 Sales Dashboard", self._show_sales_dashboard),
            ("📦 Inventory", self._show_inventory),
            ("📁 Categories", self._show_categories),
            ("👥 Users", self._show_users),
            ("💾 Backup / Restore", self._show_backup),
            ("📝 Audit Log", self._show_audit_log),
            ("↩️ Returns", self._open_returns),
        ]
        if self.user["role"] == "god":
            buttons.insert(5, ("🔑 Reset Password", self._show_reset_pw))

        for text, cmd in buttons:
            ctk.CTkButton(sb, text=text, fg_color="transparent", text_color=("gray10", "gray90"),
                          hover_color=("gray80", "gray30"), anchor="w", command=cmd).pack(fill="x", padx=12, pady=2)

        ctk.CTkButton(sb, text="🚪 Logout", font=("Arial", 14, "bold"), fg_color="#e74c3c", hover_color="#c0392b", command=self.on_logout).pack(side="bottom", fill="x", padx=12, pady=16)
        
        # Appearance Mode Menu
        self.theme_menu = ctk.CTkOptionMenu(sb, values=["Light", "Dark", "System"], command=self._set_theme)
        cur_mode = ctk.get_appearance_mode().capitalize()
        self.theme_menu.set(cur_mode if cur_mode in ["Light", "Dark"] else "Light")
        self.theme_menu.pack(side="bottom", fill="x", padx=12, pady=(0, 5))
        self._set_theme(self.theme_menu.get()) # Initial style setup

    def _build_content(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True, padx=16, pady=16)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # =========== INVENTORY ===========
    def _show_inventory(self):
        self._clear_content()
        
        # Main outer card for the inventory section
        main_card = ctk.CTkFrame(self.content, fg_color=("white", "gray20"), corner_radius=20, border_width=1, border_color=("#e5e7eb", "gray30"))
        main_card.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header row inside the card
        header = ctk.CTkFrame(main_card, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(header, text="📦 Inventory", font=("Arial", 28, "bold"), text_color=("#111827", "#f9fafb")).pack(side="left")
        
        # Header buttons
        ctk.CTkButton(header, text="➕Add Item", font=("Arial", 15, "bold"), 
                      fg_color="#36dac5", hover_color="#2eb3a2", text_color="white",
                      width=130, height=45, corner_radius=10, command=self._add_item_dialog).pack(side="right")
        
        ctk.CTkButton(header, text="📥Import CSV", font=("Arial", 14),
                      fg_color=("white", "gray30"), border_width=1, border_color=("#d1d5db", "gray40"),
                      text_color=("#374151", "#f3f4f6"), hover_color=("#f9fafb", "gray40"),
                      width=120, height=45, corner_radius=10, command=self._import_csv).pack(side="right", padx=10)

        ctk.CTkButton(header, text="📤Export CSV", font=("Arial", 14),
                      fg_color=("white", "gray30"), border_width=1, border_color=("#d1d5db", "gray40"),
                      text_color=("#374151", "#f3f4f6"), hover_color=("#f9fafb", "gray40"),
                      width=120, height=45, corner_radius=10, command=self._export_csv).pack(side="right")

        # Filters and Controls row
        filt_row = ctk.CTkFrame(main_card, fg_color="transparent")
        filt_row.pack(fill="x", padx=30, pady=(0, 20))
        
        self.search_var = ctk.StringVar()
        se = ctk.CTkEntry(filt_row, placeholder_text="🔍 Search stock items...", 
                          textvariable=self.search_var, width=320, height=45, corner_radius=8,
                          border_color=("#d1d5db", "gray40"), fg_color=("white", "gray25"), font=("Arial", 15))
        se.pack(side="left")
        se.bind("<KeyRelease>", lambda e: self._refresh_items())

        # Category and Sort ComboBoxes
        cats = db.list_categories()
        cat_names = ["All Categories"] + [c["name"] for c in cats]
        self.cat_filter = ctk.CTkComboBox(filt_row, values=cat_names, width=220, height=45, corner_radius=8,
                                         border_color=("#d1d5db", "gray40"), fg_color=("white", "gray25"), font=("Arial", 14),
                                         command=lambda _: self._refresh_items())
        self.cat_filter.set("All Categories")
        self.cat_filter.pack(side="left", padx=12)

        sort_opts = ["Date ↓", "Date ↑", "Name ↓", "Name ↑", "Price ↓", "Price ↑"]
        self.sort_combo = ctk.CTkComboBox(filt_row, values=sort_opts, width=170, height=45, corner_radius=8,
                                         border_color=("#d1d5db", "gray40"), fg_color=("white", "gray25"), font=("Arial", 14),
                                         command=self._on_sort_change)
        self.sort_combo.set("Date ↓")
        self.sort_combo.pack(side="left")

        # Table Section
        table_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        
        apply_table_theme()
        
        cols = ("pid", "name", "category", "size", "price", "stock", "date")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="extended")
        for c, h, w in zip(cols, ["ID", "Name", "Category", "Size", "Price", "Stock", "Date Added"], 
                            [80, 220, 140, 80, 90, 80, 140]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, minwidth=60)
        self.tree.pack(fill="both", expand=True)

        # Action Buttons row
        btn_row = ctk.CTkFrame(main_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(10, 30))
        
        ctk.CTkButton(btn_row, text="✏️Edit Product", font=("Arial", 15, "bold"),
                      fg_color=("white", "gray30"), border_width=1, border_color=("#d1d5db", "gray40"),
                      text_color=("#374151", "#f9fafb"), hover_color=("#f3f4f6", "gray40"),
                      width=160, height=45, corner_radius=10, command=self._edit_item_dialog).pack(side="left")
        
        ctk.CTkButton(btn_row, text="🗑️Delete Item", font=("Arial", 15, "bold"),
                      fg_color="#fee2e2", text_color="#dc2626", hover_color="#fecaca",
                      width=150, height=45, corner_radius=10, command=self._delete_item).pack(side="left", padx=12)

        self._refresh_items()

    def _on_sort_change(self, val):
        mapping = {"Date ↓": ("date_added", "DESC"), "Date ↑": ("date_added", "ASC"),
                   "Name ↓": ("name", "DESC"), "Name ↑": ("name", "ASC"),
                   "Price ↓": ("price", "DESC"), "Price ↑": ("price", "ASC"),
                   "Category ↓": ("category", "DESC"), "Category ↑": ("category", "ASC")}
        self.sort_by, self.sort_dir = mapping.get(val, ("date_added", "DESC"))
        self._refresh_items()

    def _get_selected_cat_id(self):
        sel = self.cat_filter.get()
        if sel == "All Categories":
            return None
        cats = db.list_categories()
        for c in cats:
            if c["name"] == sel:
                return c["id"]
        return None

    def _refresh_items(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        items = inv.search(self._get_selected_cat_id(), self.search_var.get(), self.sort_by, self.sort_dir)
        for it in items:
            self.tree.insert("", "end", iid=it["id"],
                             values=(it["product_id"], it["name"], it["category_name"] or "—",
                                     it["size"], f"${it['price']:.2f}", it["stock"], it["date_added"]))

    def _add_item_dialog(self):
        if not db.list_categories():
            messagebox.showwarning("No Categories", "No categories found! Please create a category first before adding items.")
            self._show_categories()
            return
        self._item_dialog("Add Item")

    def _edit_item_dialog(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Select", "Select an item first.")
        item_id = int(sel[0])
        vals = self.tree.item(item_id, "values")
        self._item_dialog("Edit Item", item_id, vals)

    def _item_dialog(self, title, item_id=None, vals=None):
        d = ctk.CTkToplevel(self)
        d.title(title)
        d.geometry("380x520")
        d.grab_set()

        ctk.CTkLabel(d, text="Product Name", font=("Arial", 14, "bold")).pack(anchor="w", padx=25, pady=(20, 5))
        name_e = ctk.CTkEntry(d, width=310, height=35, corner_radius=8)
        name_e.pack(padx=25)

        ctk.CTkLabel(d, text="Category", font=("Arial", 14, "bold")).pack(anchor="w", padx=25, pady=(15, 5))
        cats = db.list_categories()
        cat_names = [c["name"] for c in cats]
        cat_cb = ctk.CTkComboBox(d, values=cat_names, width=310, height=35, corner_radius=8)
        cat_cb.pack(padx=25)

        ctk.CTkLabel(d, text="Price ($)", font=("Arial", 14, "bold")).pack(anchor="w", padx=25, pady=(15, 5))
        price_e = ctk.CTkEntry(d, width=310, height=35, corner_radius=8)
        price_e.pack(padx=25)

        ctk.CTkLabel(d, text="Initial Stock", font=("Arial", 14, "bold")).pack(anchor="w", padx=25, pady=(15, 5))
        stock_e = ctk.CTkEntry(d, width=310, height=35, corner_radius=8)
        stock_e.pack(padx=25)

        ctk.CTkLabel(d, text="Size (e.g. L, XL, na)", font=("Arial", 14, "bold")).pack(anchor="w", padx=25, pady=(15, 5))
        size_e = ctk.CTkEntry(d, width=310, height=35, corner_radius=8)
        size_e.pack(padx=25)

        if vals:
            name_e.insert(0, vals[1])
            cat_cb.set(vals[2])
            size_e.insert(0, vals[3])
            price_e.insert(0, vals[4].replace("$", ""))
            stock_e.insert(0, vals[5])
        else:
            if cat_names:
                cat_cb.set(cat_names[0])
            stock_e.insert(0, "0")
            size_e.insert(0, "na")

        def save():
            n = name_e.get().strip()
            p = price_e.get().strip()
            s = stock_e.get().strip()
            sz = size_e.get().strip() or "na"
            cat_sel = cat_cb.get()

            if not n or not p or not cat_sel:
                return messagebox.showwarning("Missing", "Name, category, and price are required.")
            
            try:
                p = float(p)
            except ValueError:
                return messagebox.showwarning("Invalid", "Price must be a number.")
            try:
                s = int(s)
            except ValueError:
                return messagebox.showwarning("Invalid", "Stock must be a whole number.")
            
            cid = None
            for c in cats:
                if c["name"] == cat_sel:
                    cid = c["id"]
            
            if cid is None:
                return messagebox.showwarning("Invalid", "Please select a valid category.")

            if item_id:
                inv.edit(item_id, n, cid, p, s, sz)
                db.log_action(self.user['username'], "EDIT_ITEM", f"Edited item ID {item_id}: {n} ({sz})")
            else:
                pid = inv.add(n, cid, p, s, sz)
                db.log_action(self.user['username'], "ADD_ITEM", f"Added item {pid}: {n} (Size: {sz}, stock: {s})")
            
            d.destroy()
            self._refresh_items()

        ctk.CTkButton(d, text="Save Product", font=("Arial", 14, "bold"), fg_color="#36dac5", hover_color="#2eb3a2",
                      width=200, height=40, corner_radius=10, command=save).pack(pady=30)

    def _delete_item(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Select", "Select at least one item first.")
        
        count = len(sel)
        msg = f"Delete this item?" if count == 1 else f"Are you sure you want to delete {count} selected items?"
        
        if messagebox.askyesno("Confirm Deletion", msg):
            item_ids = [int(iid) for iid in sel]
            inv.remove_multiple(item_ids)
            
            # Log the action (summary)
            detail = f"Deleted item ID {sel[0]}" if count == 1 else f"Bulk deleted {count} items"
            db.log_action(self.user['username'], "DELETE_ITEMS", detail)
            
            self._refresh_items()

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            inv.export_csv(path)
            db.log_action(self.user['username'], "EXPORT_CSV", f"Exported inventory to {path}")
            messagebox.showinfo("Done", f"Exported to {path}")

    def _import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return

        try:
            items, new_cats = db.preview_items_csv(path)
            
            def finalize():
                try:
                    new_cnt, upd_cnt = inv.import_csv(path)
                    db.log_action(self.user['username'], "IMPORT_CSV", f"Imported from {path}: {new_cnt} new, {upd_cnt} updated")
                    messagebox.showinfo("Import Successful", 
                                        f"CSV Import Complete!\n\nAdded: {new_cnt} new items\nUpdated: {upd_cnt} existing items")
                    self._refresh_items()
                except Exception as ex:
                    messagebox.showerror("Import Error", f"Failed to save items:\n{str(ex)}")

            # Show the preview dialog
            ImportPreviewDialog(self, items, new_cats, finalize)

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read CSV:\n{str(e)}")

    # =========== CATEGORIES ===========
    def _show_categories(self):
        self._clear_content()
        
        # Main outer card
        main_card = ctk.CTkFrame(self.content, fg_color=("white", "gray20"), corner_radius=20, border_width=1, border_color=("#e5e7eb", "gray30"))
        main_card.pack(fill="both", expand=True, padx=20, pady=20)

        # Header inside the card
        header = ctk.CTkFrame(main_card, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        ctk.CTkLabel(header, text="📁 Categories", font=("Arial", 28, "bold"), text_color=("#111827", "#f9fafb")).pack(side="left")

        # Top row for adding new categories
        top = ctk.CTkFrame(main_card, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(0, 20))
        
        self.cat_entry = ctk.CTkEntry(top, placeholder_text="New category name...", 
                                      width=320, height=45, corner_radius=8, font=("Arial", 15),
                                      border_color=("#d1d5db", "gray40"), fg_color=("white", "gray25"))
        self.cat_entry.pack(side="left")
        
        ctk.CTkButton(top, text="➕Add Category", font=("Arial", 15, "bold"),
                      fg_color="#36dac5", hover_color="#2eb3a2", text_color="white",
                      width=160, height=45, corner_radius=10, command=self._add_cat).pack(side="left", padx=12)

        # Scrollable list within the card
        list_container = ctk.CTkFrame(main_card, fg_color="transparent")
        list_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.cat_list = ctk.CTkScrollableFrame(list_container, fg_color=("white", "gray25"), 
                                               corner_radius=10, border_width=1, border_color=("#e5e7eb", "gray30"))
        self.cat_list.pack(fill="both", expand=True)
        self._refresh_cats()

    def _refresh_cats(self):
        for w in self.cat_list.winfo_children():
            w.destroy()
        for c in db.list_categories():
            row = ctk.CTkFrame(self.cat_list, fg_color="transparent")
            row.pack(fill="x", pady=6, padx=10)
            
            ctk.CTkLabel(row, text=f"🏷️ {c['name']}", font=("Arial", 14)).pack(side="left", padx=8)
            
            # Actions
            ctk.CTkButton(row, text="🗑️", width=35, height=35, corner_radius=8,
                          fg_color="#fee2e2", text_color="#dc2626", hover_color="#fecaca",
                          command=lambda cid=c["id"]: self._del_cat(cid)).pack(side="right", padx=4)
            ctk.CTkButton(row, text="✏️", width=35, height=35, corner_radius=8,
                          fg_color=("white", "gray35"), border_width=1, border_color=("#d1d5db", "gray45"),
                          text_color=("#374151", "#f9fafb"), hover_color=("#f3f4f6", "gray45"),
                          command=lambda cid=c["id"], cn=c["name"]: self._edit_cat(cid, cn)).pack(side="right")

    def _add_cat(self):
        name = self.cat_entry.get().strip()
        if name:
            if not db.add_category(name):
                messagebox.showwarning("Exists", "Category already exists.")
            else:
                db.log_action(self.user['username'], "ADD_CATEGORY", f"Added category: {name}")
            self.cat_entry.delete(0, "end")
            self._refresh_cats()

    def _del_cat(self, cid):
        if messagebox.askyesno("Confirm", "Delete this category?"):
            db.delete_category(cid)
            db.log_action(self.user['username'], "DELETE_CATEGORY", f"Deleted category ID {cid}")
            self._refresh_cats()

    def _edit_cat(self, cid, old_name):
        d = ctk.CTkToplevel(self)
        d.title("Edit Category")
        d.geometry("300x140")
        d.grab_set()
        e = ctk.CTkEntry(d, width=250)
        e.pack(pady=20, padx=20)
        e.insert(0, old_name)

        def save():
            n = e.get().strip()
            if n:
                db.update_category(cid, n)
            d.destroy()
            self._refresh_cats()

        ctk.CTkButton(d, text="Save", command=save).pack()

    # =========== USERS ===========
    def _show_users(self):
        self._clear_content()

        # Main outer card
        main_card = ctk.CTkFrame(self.content, fg_color=("white", "gray20"), corner_radius=20, border_width=1, border_color=("#e5e7eb", "gray30"))
        main_card.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Row
        header = ctk.CTkFrame(main_card, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        ctk.CTkLabel(header, text="👥 User Management", font=("Arial", 28, "bold"), text_color=("#111827", "#f9fafb")).pack(side="left")

        # Creation Form row
        form = ctk.CTkFrame(main_card, fg_color="transparent")
        form.pack(fill="x", padx=30, pady=(0, 20))
        
        self.new_user_e = ctk.CTkEntry(form, placeholder_text="Username", width=180, height=45, corner_radius=8, font=("Arial", 15),
                                      border_color=("#d1d5db", "gray40"), fg_color=("white", "gray25"))
        self.new_user_e.pack(side="left")
        
        self.new_pass_e = ctk.CTkEntry(form, placeholder_text="Password", show="•", width=180, height=45, corner_radius=8, font=("Arial", 15),
                                      border_color=("#d1d5db", "gray40"), fg_color=("white", "gray25"))
        self.new_pass_e.pack(side="left", padx=10)
        
        self.new_role_cb = ctk.CTkComboBox(form, values=["cashier", "admin"], width=130, height=45, corner_radius=8, font=("Arial", 14),
                                          border_color=("#d1d5db", "gray40"), fg_color=("white", "gray25"))
        self.new_role_cb.set("cashier")
        self.new_role_cb.pack(side="left", padx=10)
        
        ctk.CTkButton(form, text="➕Create User", font=("Arial", 15, "bold"),
                      fg_color="#36dac5", hover_color="#2eb3a2", text_color="white",
                      width=160, height=45, corner_radius=10, command=self._create_user).pack(side="left")

        # Scrollable list within the card
        list_container = ctk.CTkFrame(main_card, fg_color="transparent")
        list_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.user_list = ctk.CTkScrollableFrame(list_container, fg_color=("white", "gray25"),
                                                corner_radius=10, border_width=1, border_color=("#e5e7eb", "gray30"))
        self.user_list.pack(fill="both", expand=True)
        self._refresh_users()

    def _refresh_users(self):
        for w in self.user_list.winfo_children():
            w.destroy()
        for u in db.list_users():
            row = ctk.CTkFrame(self.user_list, fg_color="transparent")
            row.pack(fill="x", pady=6, padx=10)
            
            icon = "🛡️" if u["role"] in ["admin", "god"] else "👤"
            ctk.CTkLabel(row, text=f"{icon} {u['username']}  ({u['role']})", font=("Arial", 15)).pack(side="left", padx=8)
            
            ctk.CTkButton(row, text="🗑️Remove", width=110, height=35, corner_radius=8, font=("Arial", 14, "bold"),
                          fg_color="#fee2e2", text_color="#dc2626", hover_color="#fecaca",
                          command=lambda uid=u["id"]: self._del_user(uid)).pack(side="right", padx=4)

    def _create_user(self):
        u = self.new_user_e.get().strip()
        p = self.new_pass_e.get().strip()
        r = self.new_role_cb.get()
        if not u or not p:
            return messagebox.showwarning("Missing", "Username and password required.")
        if not auth.register_user(u, p, r):
            return messagebox.showwarning("Exists", "Username already taken.")
        db.log_action(self.user['username'], "CREATE_USER", f"Created user '{u}' with role '{r}'")
        self.new_user_e.delete(0, "end")
        self.new_pass_e.delete(0, "end")
        self._refresh_users()

    def _del_user(self, uid):
        if uid == self.user["id"]:
            return messagebox.showwarning("Denied", "You cannot delete your own account.")
            
        # check if it's the last admin
        users = db.list_users()
        admins = [u for u in users if u["role"] == "admin"]
        target = next((u for u in users if u["id"] == uid), None)
        
        if target and target["role"] == "admin" and len(admins) <= 1:
            return messagebox.showwarning("Denied", "You cannot delete the last admin account.")

        if messagebox.askyesno("Confirm", "Delete this user?"):
            db.delete_user(uid)
            db.log_action(self.user['username'], "DELETE_USER", f"Deleted user ID {uid}")
            self._refresh_users()

    # =========== RESET PASSWORD (god) ===========
    def _show_reset_pw(self):
        self._clear_content()
        ctk.CTkLabel(self.content, text="Reset Password", font=("", 20, "bold")).pack(anchor="w")
        users = db.list_users(exclude_god=False)
        names = [u["username"] for u in users]
        self.rp_user = ctk.CTkComboBox(self.content, values=names, width=220)
        self.rp_user.pack(pady=10)
        self.rp_pass = ctk.CTkEntry(self.content, placeholder_text="New password", show="•", width=220)
        self.rp_pass.pack(pady=6)

        def do_reset():
            u = self.rp_user.get()
            p = self.rp_pass.get().strip()
            if not p:
                return messagebox.showwarning("Missing", "Enter new password.")
            auth.reset_password(u, p)
            db.log_action(self.user['username'], "RESET_PASSWORD", f"Reset password for '{u}'")
            messagebox.showinfo("Done", f"Password reset for {u}.")

        ctk.CTkButton(self.content, text="Reset", command=do_reset).pack(pady=10)

    # =========== BACKUP ===========
    def _show_backup(self):
        self._clear_content()
        
        card = ctk.CTkFrame(self.content, fg_color=("white", "gray20"), corner_radius=20, border_width=1, border_color=("#e5e7eb", "gray30"))
        card.pack(fill="x", expand=False, padx=10, pady=10)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(25, 20))
        ctk.CTkLabel(header, text="💾 Database Backup & Restore", font=("Arial", 22, "bold")).pack(side="left")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=25, pady=(0, 25))

        ctk.CTkButton(btn_row, text="📤Create Backup", width=180, height=50, corner_radius=12,
                      fg_color="#36dac5", hover_color="#2eb3a2", font=("Arial", 15, "bold"),
                      command=self._do_backup).pack(side="left", padx=(0, 15))

        ctk.CTkButton(btn_row, text="📥Restore Backup", width=180, height=50, corner_radius=12,
                      fg_color="#fef3c7", text_color="#d97706", hover_color="#fde68a", font=("Arial", 15, "bold"),
                      command=self._do_restore).pack(side="left")

    def _do_backup(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB", "*.db")])
        if path:
            # Using internal database backup logic
            import shutil
            try:
                shutil.copy2("inventory.db", path)
                db.log_action(self.user['username'], "BACKUP_DB", f"Backed up to {path}")
                messagebox.showinfo("Done", f"Backup saved to {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Backup failed: {e}")

    def _do_restore(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if path:
            if messagebox.askyesno("Confirm", "This will overwrite current data. Application will close. Continue?"):
                import shutil
                try:
                    # In a real app we'd close connections first
                    shutil.copy2(path, "inventory.db")
                    db.log_action(self.user['username'], "RESTORE_DB", f"Restored from {path}")
                    messagebox.showinfo("Done", "Database restored. Application will now close.")
                    self.master.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Restore failed: {e}")

    # =========== SALES DASHBOARD ===========
    def _show_sales_dashboard(self):
        self._clear_content()
        ctk.CTkLabel(self.content, text="📊 Sales Dashboard", font=("", 28, "bold")).pack(anchor="w", pady=(10, 0), padx=10)

        # --- Summary Cards ---
        cards_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(20, 20), padx=10)
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        periods = [
            ("Today", "today"),
            ("This Week", "week"),
            ("This Month", "month"),
            ("All Time", "all"),
        ]
        colors = ["#27ae60", "#2980b9", "#8e44ad", "#e67e22"]
        icons = ["💵", "📈", "📅", "🏆"]

        for col, ((label, period), color, icon) in enumerate(zip(periods, colors, icons)):
            summary = db.get_sales_summary(period)
            card = ctk.CTkFrame(cards_frame, corner_radius=15, fg_color=("white", "gray20"), border_width=1, border_color=("#e5e7eb", "gray30"))
            card.grid(row=0, column=col, sticky="nsew", padx=10)
            
            top_bar = ctk.CTkFrame(card, fg_color="transparent")
            top_bar.pack(fill="x", padx=15, pady=(15, 0))
            ctk.CTkLabel(top_bar, text=label, font=("Arial", 13), text_color=("gray", "gray80")).pack(side="left")
            
            icon_badge = ctk.CTkFrame(top_bar, fg_color=color, corner_radius=8, width=28, height=28)
            icon_badge.pack(side="right")
            icon_badge.pack_propagate(False)
            ctk.CTkLabel(icon_badge, text=icon, font=("", 12)).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(card, text=f"${summary['revenue']:.2f}",
                         font=("Arial", 26, "bold"), text_color=("black", "white")).pack(anchor="w", padx=15, pady=(5, 0))
            ctk.CTkLabel(card, text=f"{summary['transactions']} transactions",
                         font=("Arial", 12), text_color=("#9ca3af", "gray60")).pack(pady=(0, 15), anchor="w", padx=15)

        # --- Two-column layout for tables ---
        tables_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        tables_frame.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tables_frame.grid_columnconfigure(0, weight=1)
        tables_frame.grid_columnconfigure(1, weight=1)
        tables_frame.grid_rowconfigure(0, weight=1)
        tables_frame.grid_rowconfigure(1, weight=1)

        # --- Top Selling Items (top-left) ---
        top_frame = ctk.CTkFrame(tables_frame, corner_radius=15, fg_color=("white", "gray20"), border_width=1, border_color=("#e5e7eb", "gray30"))
        top_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        ctk.CTkLabel(top_frame, text="🔥 Top Selling Items", font=("Arial", 18, "bold"), text_color=("#34495e", "gray90")).pack(anchor="w", padx=20, pady=(20, 10))

        top_cols = ("name", "sold", "revenue")
        top_tree = ttk.Treeview(top_frame, columns=top_cols, show="headings", height=6)
        for c, h, w in zip(top_cols, ["Item", "Qty Sold", "Revenue"], [220, 90, 120]):
            top_tree.heading(c, text=h)
            top_tree.column(c, width=w, minwidth=60)
        top_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for item in db.get_top_selling_items(8):
            top_tree.insert("", "end", values=(
                item["name"], item["total_sold"], f"${item['total_revenue']:.2f}"))

        # --- Worst Selling Items (top-right) ---
        worst_frame = ctk.CTkFrame(tables_frame, corner_radius=15, fg_color=("white", "gray20"), border_width=1, border_color=("#e5e7eb", "gray30"))
        worst_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        ctk.CTkLabel(worst_frame, text="📉 Worst Selling Items", font=("Arial", 18, "bold"), text_color=("#34495e", "gray90")).pack(anchor="w", padx=20, pady=(20, 10))

        worst_cols = ("name", "sold", "revenue")
        worst_tree = ttk.Treeview(worst_frame, columns=worst_cols, show="headings", height=6)
        for c, h, w in zip(worst_cols, ["Item", "Qty Sold", "Revenue"], [220, 90, 120]):
            worst_tree.heading(c, text=h)
            worst_tree.column(c, width=w, minwidth=60)
        worst_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for item in db.get_worst_selling_items(8):
            worst_tree.insert("", "end", values=(
                item["name"], item["product_id"], item["total_sold"]))

        # --- Recent Transactions (bottom-left) ---
        recent_frame = ctk.CTkFrame(tables_frame, corner_radius=15, fg_color=("white", "gray20"), border_width=1, border_color=("#e5e7eb", "gray30"))
        recent_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        ctk.CTkLabel(recent_frame, text="🧾 Recent Transactions", font=("Arial", 18, "bold"), text_color=("#34495e", "gray90")).pack(anchor="w", padx=20, pady=(20, 10))

        recent_cols = ("detail", "qty", "amount", "date")
        recent_tree = ttk.Treeview(recent_frame, columns=recent_cols, show="headings", height=8)
        for c, h, w in zip(recent_cols, ["Invoice / Item", "Qty", "Amount", "Date"], [200, 50, 90, 160]):
            recent_tree.heading(c, text=h)
            recent_tree.column(c, width=w, minwidth=40)
        recent_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for inv_item in db.get_recent_invoices(10):
            # Invoice parent row
            parent = recent_tree.insert("", "end", values=(
                f"📄 {inv_item['invoice_number']}  ({inv_item['cashier_username']})",
                "", f"${inv_item['total_amount']:.2f}", inv_item["date_created"]))
            # Item child rows
            for sold in inv_item["items"]:
                recent_tree.insert(parent, "end", values=(
                    f"   ↳ {sold['name']}", sold["quantity"],
                    f"${sold['price'] * sold['quantity']:.2f}", ""))

        # --- Low Stock Alerts (bottom-right) ---
        low_frame = ctk.CTkFrame(tables_frame, corner_radius=15, fg_color=("white", "gray20"), border_width=1, border_color=("#e5e7eb", "gray30"))
        low_frame.grid(row=1, column=1, sticky="nsew", padx=15, pady=15)
        ctk.CTkLabel(low_frame, text="⚠️ Low Stock Alerts", font=("Arial", 18, "bold"), text_color="#e74c3c").pack(anchor="w", padx=20, pady=(20, 10))

        low_cols = ("name", "pid", "stock")
        low_tree = ttk.Treeview(low_frame, columns=low_cols, show="headings", height=6)
        for c, h, w in zip(low_cols, ["Item", "Product ID", "Stock"], [220, 120, 90]):
            low_tree.heading(c, text=h)
            low_tree.column(c, width=w, minwidth=60)
        low_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        low_stock = db.get_low_stock_items(5)
        for item in low_stock:
            low_tree.insert("", "end", values=(
                item["name"], item["product_id"], item["stock"]))

        if not low_stock:
            ctk.CTkLabel(low_frame, text="✅ All items well stocked!",
                         text_color="#27ae60", font=("", 12)).pack(pady=10)

    # =========== RETURNS ===========
    def _open_returns(self):
        from ui.return_dialog import ReturnDialog
        
        def on_success():
            if hasattr(self, "tree") and self.tree.winfo_exists():
                self._refresh_items()

        ReturnDialog(self, self.user["username"], on_refund_success=on_success)

    # =========== AUDIT LOG ===========
    def _show_audit_log(self):
        self._clear_content()
        
        card = ctk.CTkFrame(self.content, fg_color=("white", "gray20"), corner_radius=20, border_width=1, border_color=("#e5e7eb", "gray30"))
        card.pack(fill="both", expand=True)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(25, 10))
        ctk.CTkLabel(header, text="📝 System Audit Log", font=("Arial", 22, "bold")).pack(side="left")
        
        # Add Export Button
        ctk.CTkButton(header, text="📥Export CSV", width=120, height=35, corner_radius=8,
                      fg_color="#36dac5", hover_color="#2eb3a2", font=("Arial", 13, "bold"),
                      command=self._export_audit_log).pack(side="right")

        table_container = ctk.CTkFrame(card, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        cols = ("stamp", "user", "action", "detail")
        tree = ttk.Treeview(table_container, columns=cols, show="headings")
        for c, h, w in zip(cols, ["Timestamp", "User", "Action", "Details"], [160, 100, 140, 350]):
            tree.heading(c, text=h)
            tree.column(c, width=w, minwidth=50)
        tree.pack(fill="both", expand=True)

        logs = db.get_audit_log(200)
        for log in logs:
            tree.insert("", "end", values=(
                log["timestamp"], log["username"], log["action"], log["detail"]))

    def _export_audit_log(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path: return
        
        import csv
        try:
            logs = db.get_audit_log(1000)
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "User", "Action", "Details"])
                for log in logs:
                    writer.writerow([log["timestamp"], log["username"], log["action"], log["detail"]])
            messagebox.showinfo("Success", f"Audit log exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def _set_theme(self, mode):
        apply_table_theme(mode)
