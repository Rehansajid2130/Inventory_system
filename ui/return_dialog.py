import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import ttk
import database as db
from ui.theme_helper import apply_table_theme

class ReturnDialog(ctk.CTkToplevel):
    def __init__(self, master, current_username, on_refund_success=None):
        super().__init__(master)
        self.title("Process Returns & Refunds")
        self.geometry("800x600")
        self.minsize(700, 500)
        
        # Make it a modal window
        self.grab_set()
        self.configure(fg_color=("#f4f7f6", "gray10"))
        
        self.current_username = current_username
        self.on_refund_success = on_refund_success
        self.current_invoice = None
        self.current_items = []

        self._build_ui()

    def _build_ui(self):
        # Header (Floating Card)
        hdr_card = ctk.CTkFrame(self, fg_color=("white", "gray20"), corner_radius=15, border_width=1, border_color=("#e5e7eb", "gray30"))
        hdr_card.pack(fill="x", padx=25, pady=(25, 10))
        
        ctk.CTkLabel(hdr_card, text="🔍 Find Invoice", font=("Arial", 18, "bold")).pack(side="left", padx=20, pady=15)
        
        self.search_entry = ctk.CTkEntry(hdr_card, placeholder_text="Invoice # (e.g. INV-000001)", width=300, height=40, corner_radius=8)
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<Return>", lambda e: self._search_invoice())
        
        ctk.CTkButton(hdr_card, text="Search", width=100, height=40, corner_radius=8, 
                      fg_color="#36dac5", hover_color="#2eb3a2", command=self._search_invoice).pack(side="left", padx=10)

        # Invoice Details Area (Card)
        self.details_card = ctk.CTkFrame(self, fg_color=("white", "gray20"), corner_radius=15, border_width=1, border_color=("#e5e7eb", "gray30"))
        self.details_card.pack(fill="x", padx=25, pady=10)
        
        self.lbl_inv_num = ctk.CTkLabel(self.details_card, text="Invoice: ---", font=("Arial", 14, "bold"))
        self.lbl_inv_num.grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        self.lbl_cashier = ctk.CTkLabel(self.details_card, text="Cashier: ---", font=("Arial", 13))
        self.lbl_cashier.grid(row=0, column=1, sticky="w", padx=20, pady=10)
        
        self.lbl_date = ctk.CTkLabel(self.details_card, text="Date: ---", font=("Arial", 13))
        self.lbl_date.grid(row=1, column=0, sticky="w", padx=20, pady=10)
        
        self.lbl_total = ctk.CTkLabel(self.details_card, text="Original Total: $0.00", text_color="#059669", font=("Arial", 14, "bold"))
        self.lbl_total.grid(row=1, column=1, sticky="w", padx=20, pady=10)

        # Items Table (Card)
        table_card = ctk.CTkFrame(self, fg_color=("white", "gray20"), corner_radius=15, border_width=1, border_color=("#e5e7eb", "gray30"))
        table_card.pack(fill="both", expand=True, padx=25, pady=10)
        
        ctk.CTkLabel(table_card, text="📦 Invoice Items", font=("Arial", 16, "bold")).pack(anchor="w", padx=20, pady=(15, 5))

        table_container = ctk.CTkFrame(table_card, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        style = ttk.Style()
        style.configure("Treeview", rowheight=35, font=("Arial", 13))
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))

        cols = ("id", "name", "size", "price", "qty", "refunded", "avail")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse")
        
        for c, h, w in zip(cols, ["ID", "Item Name", "Size", "Price", "Qty", "Ref'd", "Eligible"], 
                            [0, 180, 70, 80, 70, 70, 70]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, minwidth=50, stretch=bool(w))
            
        self.tree.column("id", width=0, stretch=False) # hide internal DB id
        self.tree.pack(fill="both", expand=True)

        # Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(5, 25))
        
        self.btn_refund_all = ctk.CTkButton(btn_frame, text="⏪ Refund Entire Invoice", font=("Arial", 14, "bold"),
                                            fg_color="#fee2e2", text_color="#dc2626", hover_color="#fecaca",
                                            width=200, height=45, corner_radius=10, 
                                            command=self._refund_all, state="disabled")
        self.btn_refund_all.pack(side="left")
        
        self.btn_refund_item = ctk.CTkButton(btn_frame, text="🔄 Refund Selected Item", font=("Arial", 14, "bold"),
                                             fg_color="#fef3c7", text_color="#d97706", hover_color="#fde68a",
                                             width=200, height=45, corner_radius=10,
                                             command=self._refund_item, state="disabled")
        self.btn_refund_item.pack(side="right")

        self._set_theme(ctk.get_appearance_mode())

    def _set_theme(self, mode):
        apply_table_theme(mode)

    def _search_invoice(self):
        inv_num = self.search_entry.get().strip()
        if not inv_num: return
        
        data = db.get_invoice_full(inv_num)
        if not data:
            messagebox.showerror("Not Found", f"Invoice {inv_num} not found.")
            return
            
        self.current_invoice = data["invoice"]
        self.current_items = data["items"]
        
        # update UI
        self.lbl_inv_num.configure(text=f"Invoice: {self.current_invoice['invoice_number']}")
        self.lbl_cashier.configure(text=f"Cashier: {self.current_invoice['cashier_username']}")
        self.lbl_date.configure(text=f"Date: {self.current_invoice['date_created']}")
        self.lbl_total.configure(text=f"Original Total: ${self.current_invoice['total_amount']:.2f}")
        
        self._refresh_table()

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        has_refundable = False
        for it in self.current_items:
            avail = it["quantity"] - it["refunded_quantity"]
            if avail > 0: has_refundable = True
            
            self.tree.insert("", "end", values=(
                it["ii_id"], it["name"], it["size"], f"${it['price_at_sale']:.2f}",
                it["quantity"], it["refunded_quantity"], avail
            ))
            
        state = "normal" if has_refundable else "disabled"
        self.btn_refund_all.configure(state=state)
        self.btn_refund_item.configure(state=state)

    def _refund_all(self):
        if not messagebox.askyesno("Confirm Full Refund", "Are you sure you want to refund ALL remaining items on this invoice?"):
            return
            
        refunds_dict = {}
        for it in self.current_items:
            avail = it["quantity"] - it["refunded_quantity"]
            if avail > 0:
                refunds_dict[it["ii_id"]] = avail
                
        if not refunds_dict: return
        
        self._execute_refund(refunds_dict)

    def _refund_item(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Select", "Please select an item to refund.")
            
        vals = self.tree.item(sel[0], "values")
        ii_id = int(vals[0])
        item_name = vals[1]
        avail = int(vals[5])
        
        if avail <= 0:
            return messagebox.showwarning("Empty", "This item has already been fully refunded.")
            
        # Ask for quantity if there's more than 1 available
        refund_qty = 1
        if avail > 1:
            dialog = ctk.CTkInputDialog(text=f"How many to refund? (1 to {avail})", title="Refund Quantity")
            ans = dialog.get_input()
            if ans is None: return # user canceled
            try:
                refund_qty = int(ans)
                if refund_qty < 1 or refund_qty > avail:
                    raise ValueError()
            except ValueError:
                return messagebox.showerror("Invalid", "Please enter a valid quantity within the allowed limit.")
                
        # confirm popup
        if messagebox.askyesno("Confirm", f"Refund {refund_qty}x {item_name}?"):
            self._execute_refund({ii_id: refund_qty})
            
    def _execute_refund(self, refunds_dict):
        try:
            total_refunded = db.process_refund(self.current_invoice["id"], refunds_dict, self.current_username)
            messagebox.showinfo("Success", f"Refund processed successfully for ${total_refunded:.2f}!")
            
            # refresh data from DB
            data = db.get_invoice_full(self.current_invoice["invoice_number"])
            self.current_invoice = data["invoice"]
            self.current_items = data["items"]
            self._refresh_table()
            
            if self.on_refund_success:
                self.on_refund_success()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process refund: {e}")
