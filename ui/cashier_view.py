import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db
import inventory as inv
from ui.theme_helper import apply_table_theme


class CashierView(ctk.CTkFrame):
    def __init__(self, master, user, on_logout):
        super().__init__(master)
        self.user = user
        self.on_logout = on_logout
        self.sort_by = "date_added"
        self.sort_dir = "DESC"
        self.cart = []  # list of dicts: {id, product_id, name, price, quantity}
        
        self.configure(fg_color=("#f4f7f6", "gray10"))
        self._build()

    def _build(self):
        # Header Row (Floating)
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkLabel(hdr, text="🛒 Cashier Terminal", font=("Arial", 28, "bold"), text_color=("#111827", "#f9fafb")).pack(side="left")
        
        # Logout & Management buttons (Right)
        ctk.CTkButton(hdr, text="🚪Logout", font=("Arial", 14, "bold"), 
                      fg_color="#fee2e2", text_color="#dc2626", hover_color="#fecaca",
                      width=100, height=40, corner_radius=10, command=self.on_logout).pack(side="right")
        
        ctk.CTkButton(hdr, text="↩️Returns", font=("Arial", 14, "bold"),
                      fg_color="#fef3c7", text_color="#d97706", hover_color="#fde68a",
                      width=100, height=40, corner_radius=10, command=self._open_returns).pack(side="right", padx=12)
        
        self.theme_menu = ctk.CTkOptionMenu(hdr, values=["Light", "Dark", "System"], command=self._set_theme, 
                                           width=100, height=40, corner_radius=10, fg_color=("white", "gray25"), 
                                           button_color=("#e5e7eb", "gray35"), button_hover_color=("#d1d5db", "gray40"), 
                                           text_color=("#374151", "#f9fafb"))
        cur_mode = ctk.get_appearance_mode().capitalize()
        self.theme_menu.set(cur_mode if cur_mode in ["Light", "Dark"] else "Light")
        self.theme_menu.pack(side="right", padx=10)
        self._set_theme(self.theme_menu.get()) # Initial style setup
        
        ctk.CTkLabel(hdr, text=f"👤 {self.user['username']}", font=("Arial", 14, "bold"), text_color="gray").pack(side="right", padx=(0, 10))

        # Main Split Frame
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        main_container.grid_columnconfigure(0, weight=3)
        main_container.grid_columnconfigure(1, weight=2)
        main_container.grid_rowconfigure(0, weight=1)

        # ===== LEFT: Inventory Card =====
        left_card = ctk.CTkFrame(main_container, fg_color=("white", "gray20"), corner_radius=20, border_width=1, border_color=("#e5e7eb", "gray30"))
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(left_card, text="📦 Browse Inventory", font=("Arial", 22, "bold"), text_color=("#1f2937", "#f3f4f6")).pack(anchor="w", padx=25, pady=(25, 15))

        # Filter bar
        filt = ctk.CTkFrame(left_card, fg_color="transparent")
        filt.pack(fill="x", padx=25, pady=(0, 15))
        
        self.search_var = ctk.StringVar()
        se = ctk.CTkEntry(filt, placeholder_text="🔍 Search stock...", textvariable=self.search_var, 
                          width=180, height=45, corner_radius=8, font=("Arial", 14))
        se.pack(side="left", fill="x", expand=True)
        se.bind("<KeyRelease>", lambda e: self._refresh())

        cats = db.list_categories()
        cat_names = ["All Categories"] + [c["name"] for c in cats]
        self.cat_filter = ctk.CTkComboBox(filt, values=cat_names, width=160, height=45, corner_radius=8, font=("Arial", 13), command=lambda _: self._refresh())
        self.cat_filter.set("All Categories")
        self.cat_filter.pack(side="left", padx=10)

        sort_opts = ["Date ↓", "Date ↑", "Name ↓", "Name ↑", "Price ↓", "Price ↑"]
        self.sort_combo = ctk.CTkComboBox(filt, values=sort_opts, width=120, height=45, corner_radius=8, font=("Arial", 13), command=self._on_sort)
        self.sort_combo.set("Date ↓")
        self.sort_combo.pack(side="left")

        # Inventory Table
        table_container = ctk.CTkFrame(left_card, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=25, pady=(0, 15))
        
        apply_table_theme()

        cols = ("pid", "name", "category", "size", "price", "stock")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse")
        for c, h, w in zip(cols, ["ID", "Product Name", "Category", "Size", "Price", "Stock"], 
                            [80, 200, 120, 70, 80, 60]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, minwidth=60)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._add_to_cart())

        # Cart Action
        add_btn_frame = ctk.CTkFrame(left_card, fg_color="transparent")
        add_btn_frame.pack(fill="x", padx=25, pady=(0, 25))
        ctk.CTkButton(add_btn_frame, text="➕Add to Cart", font=("Arial", 15, "bold"), 
                      fg_color="#36dac5", hover_color="#2eb3a2", text_color="white",
                      width=180, height=50, corner_radius=12, command=self._add_to_cart).pack(side="left")

        # ===== RIGHT: Cart Card =====
        right_card = ctk.CTkFrame(main_container, fg_color=("white", "gray20"), corner_radius=20, border_width=1, border_color=("#e5e7eb", "gray30"))
        right_card.grid(row=0, column=1, sticky="nsew")

        right_header = ctk.CTkFrame(right_card, fg_color="transparent")
        right_header.pack(fill="x", padx=25, pady=(25, 15))
        ctk.CTkLabel(right_header, text="🛒 Shopping Cart", font=("Arial", 22, "bold"), text_color=("#1f2937", "#f3f4f6")).pack(side="left")
        
        ctk.CTkButton(right_header, text="🗑️Clear",
                      fg_color="#fee2e2", text_color="#dc2626", hover_color="#fecaca",
                      height=35, corner_radius=8, command=self._clear_cart).pack(side="right")

        # Cart Table
        cart_table_container = ctk.CTkFrame(right_card, fg_color="transparent")
        cart_table_container.pack(fill="both", expand=True, padx=25, pady=(0, 15))
        
        cart_cols = ("name", "size", "qty", "price", "subtotal")
        self.cart_tree = ttk.Treeview(cart_table_container, columns=cart_cols, show="headings", selectmode="browse")
        for c, h, w in zip(cart_cols, ["Item", "Size", "Qty", "Price", "Subtotal"], 
                            [150, 60, 60, 80, 100]):
            self.cart_tree.heading(c, text=h)
            self.cart_tree.column(c, width=w, minwidth=50)
        self.cart_tree.pack(fill="both", expand=True)

        # Cart Management row
        cart_btns = ctk.CTkFrame(right_card, fg_color="transparent")
        cart_btns.pack(fill="x", padx=25, pady=(0, 15))
        
        ctk.CTkButton(cart_btns, text="➕", width=40, height=40, font=("", 15, "bold"),
                      fg_color=("white", "gray35"), border_width=1, border_color=("#d1d5db", "gray45"),
                      text_color=("#374151", "#f9fafb"), hover_color=("#f3f4f6", "gray45"),
                      command=self._increase_qty).pack(side="left", padx=(0, 8))
        
        ctk.CTkButton(cart_btns, text="➖", width=40, height=40, font=("", 15, "bold"),
                      fg_color=("white", "gray35"), border_width=1, border_color=("#d1d5db", "gray45"),
                      text_color=("#374151", "#f9fafb"), hover_color=("#f3f4f6", "gray45"),
                      command=self._decrease_qty).pack(side="left")
        
        ctk.CTkButton(cart_btns, text="🗑️Remove", height=40,
                      fg_color="#fee2e2", text_color="#dc2626", hover_color="#fecaca",
                      command=self._remove_from_cart).pack(side="left", padx=12)

        # Total Section
        self.total_var = ctk.StringVar(value="Total: $0.00")
        total_frame = ctk.CTkFrame(right_card, fg_color=("#f9fafb", "gray25"), corner_radius=12)
        total_frame.pack(fill="x", padx=25, pady=(10, 20))
        
        ctk.CTkLabel(total_frame, textvariable=self.total_var, font=("Arial", 26, "bold"),
                     text_color="#059669").pack(padx=20, pady=15)

        # Checkout Button
        ctk.CTkButton(right_card, text="💳Checkout & Print Invoice", height=60,
                      font=("Arial", 18, "bold"), fg_color="#36dac5", hover_color="#2eb3a2",
                      corner_radius=15, command=self._checkout).pack(fill="x", padx=25, pady=(0, 25))

        self._refresh()

    # ---- inventory helpers ----
    def _on_sort(self, val):
        mapping = {"Date ↓": ("date_added", "DESC"), "Date ↑": ("date_added", "ASC"),
                   "Name ↓": ("name", "DESC"), "Name ↑": ("name", "ASC"),
                   "Price ↓": ("price", "DESC"), "Price ↑": ("price", "ASC")}
        self.sort_by, self.sort_dir = mapping.get(val, ("date_added", "DESC"))
        self._refresh()

    def _refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cat_sel = self.cat_filter.get()
        cid = None
        if cat_sel != "All Categories":
            for c in db.list_categories():
                if c["name"] == cat_sel:
                    cid = c["id"]
        items = inv.search(cid, self.search_var.get(), self.sort_by, self.sort_dir)
        for it in items:
            self.tree.insert("", "end", iid=it["id"],
                             values=(it["product_id"], it["name"],
                                     it["category_name"] or "—", it["size"], f"${it['price']:.2f}", it["stock"]))

    # ---- cart helpers ----
    def _add_to_cart(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Select", "Select an item from the inventory first.")
        item_id = int(sel[0])
        vals = self.tree.item(item_id, "values")
        stock = int(vals[5])

        # check if already in cart
        for ci in self.cart:
            if ci["id"] == item_id:
                if ci["quantity"] >= stock:
                    return messagebox.showwarning("Stock Limit", f"Only {stock} left in stock.")
                ci["quantity"] += 1
                self._refresh_cart()
                return

        # new to cart
        if stock <= 0:
            return messagebox.showwarning("Out of Stock", "This item is out of stock.")
        price = float(vals[4].replace("$", ""))
        self.cart.append({
            "id": item_id,
            "product_id": vals[0],
            "name": vals[1],
            "size": vals[3],
            "price": price,
            "quantity": 1
        })
        self._refresh_cart()

    def _increase_qty(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        # Get index from the iid we set as integer
        idx = int(sel[0])
        ci = self.cart[idx]
        it = db.get_item_by_id(ci["id"])
        if it and ci["quantity"] >= it["stock"]:
            return messagebox.showwarning("Stock Limit", f"Only {it['stock']} left in stock.")
        ci["quantity"] += 1
        self._refresh_cart()

    def _decrease_qty(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        ci = self.cart[idx]
        if ci["quantity"] <= 1:
            self.cart.pop(idx)
        else:
            ci["quantity"] -= 1
        self._refresh_cart()

    def _remove_from_cart(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self.cart.pop(idx)
        self._refresh_cart()

    def _clear_cart(self):
        if self.cart and messagebox.askyesno("Confirm", "Clear all items from cart?"):
            self.cart.clear()
            self._refresh_cart()

    def _refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        total = 0.0
        for i, ci in enumerate(self.cart):
            subtotal = ci["price"] * ci["quantity"]
            total += subtotal
            self.cart_tree.insert("", "end", iid=str(i),
                                  values=(ci["name"], ci["size"], ci["quantity"],
                                          f"${ci['price']:.2f}", f"${subtotal:.2f}"))
        self.total_var.set(f"Total: ${total:.2f}")

    def _checkout(self):
        if not self.cart:
            return messagebox.showwarning("Empty Cart", "Add items to the cart before checking out.")
        total = sum(ci["price"] * ci["quantity"] for ci in self.cart)

        if not messagebox.askyesno("Confirm Checkout",
                                    f"Complete checkout for ${total:.2f}?\n\nThis will generate and print an invoice."):
            return

        try:
            filepath = inv.checkout(self.cart, self.user["username"], total)
            self.cart.clear()
            self._refresh_cart()
            self._refresh()  # refresh inventory to show updated stock
            messagebox.showinfo("Success",
                                f"Invoice generated and opened!\n\nSaved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Checkout failed:\n{e}")

    def _open_returns(self):
        from ui.return_dialog import ReturnDialog
        ReturnDialog(self, self.user["username"], on_refund_success=self._refresh)

    def _set_theme(self, mode):
        apply_table_theme(mode)

