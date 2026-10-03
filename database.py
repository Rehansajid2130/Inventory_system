import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','cashier','god'))
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category_id INTEGER,
            price REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 100,
            size TEXT DEFAULT 'na',
            date_added TEXT NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            cashier_username TEXT NOT NULL,
            total_amount REAL NOT NULL,
            date_created TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            item_id INTEGER, -- Nullable to allow item deletion without losing sales history
            name_at_sale TEXT,
            size_at_sale TEXT,
            quantity INTEGER NOT NULL,
            price_at_sale REAL NOT NULL,
            refunded_quantity INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT,
            timestamp TEXT NOT NULL
        );
    """)
    conn.commit()
    
    # --- Migration: Handle Nullable item_id in invoice_items if needed ---
    info = conn.execute("PRAGMA table_info(invoice_items)").fetchall()
    item_id_info = next((col for col in info if col["name"] == "item_id"), None)
    
    if item_id_info and item_id_info["notnull"] == 1:
        # Need to migrate to nullable item_id
        try:
            conn.execute("BEGIN TRANSACTION")
            conn.execute("PRAGMA foreign_keys=OFF")
            
            # Create temp table with NULLABLE item_id
            conn.execute("""
                CREATE TABLE invoice_items_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    item_id INTEGER,
                    name_at_sale TEXT,
                    size_at_sale TEXT,
                    quantity INTEGER NOT NULL,
                    price_at_sale REAL NOT NULL,
                    refunded_quantity INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                    FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE SET NULL
                )
            """)
            
            # Map existing columns
            cols = [c["name"] for c in info if c["name"] in 
                    ['id', 'invoice_id', 'item_id', 'name_at_sale', 'size_at_sale', 'quantity', 'price_at_sale', 'refunded_quantity']]
            cols_str = ", ".join(cols)
            
            conn.execute(f"INSERT INTO invoice_items_temp ({cols_str}) SELECT {cols_str} FROM invoice_items")
            conn.execute("DROP TABLE invoice_items")
            conn.execute("ALTER TABLE invoice_items_temp RENAME TO invoice_items")
            
            conn.commit()
            conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            conn.rollback()
            conn.execute("PRAGMA foreign_keys=ON")

    # --- Other Migrations ---
    try:
        conn.execute("ALTER TABLE items ADD COLUMN stock INTEGER NOT NULL DEFAULT 100")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE invoice_items ADD COLUMN name_at_sale TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE invoice_items ADD COLUMN size_at_sale TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE items ADD COLUMN size TEXT DEFAULT 'na'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def log_action(username, action, detail=""):
    """Record an action in the audit log."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO audit_log(username, action, detail, timestamp) VALUES(?,?,?,?)",
            (username, action, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    finally:
        conn.close()


def get_audit_log(limit=100):
    """Get recent audit log entries."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT username, action, detail, timestamp
        FROM audit_log
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- users ----------
def get_user(username):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(username, password_hash, role):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                      (username, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def list_users(exclude_god=True):
    conn = get_connection()
    q = "SELECT id,username,role FROM users"
    if exclude_god:
        q += " WHERE role != 'god'"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM users WHERE id=? AND role!='god'", (user_id,))
        conn.commit()
    finally:
        conn.close()


def update_password(username, new_hash):
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET password_hash=? WHERE username=?", (new_hash, username))
        conn.commit()
    finally:
        conn.close()


# ---------- categories ----------
def list_categories():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_category(name):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO categories(name) VALUES(?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_category(cat_id, name):
    conn = get_connection()
    try:
        conn.execute("UPDATE categories SET name=? WHERE id=?", (name, cat_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_category(cat_id):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


# ---------- items ----------
def _generate_product_id(conn):
    row = conn.execute("SELECT MAX(id) as max_id FROM items").fetchone()
    next_id = (row["max_id"] or 0) + 1
    return f"PRD-{next_id:05d}"


def add_item(name, category_id, price, stock=0, size='na'):
    conn = get_connection()
    pid = _generate_product_id(conn)
    conn.execute(
        "INSERT INTO items(product_id,name,category_id,price,stock,size,date_added) VALUES(?,?,?,?,?,?,?)",
        (pid, name, category_id if category_id else None, price, stock, size, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    return pid


def update_item(item_id, name, category_id, price, stock, size='na'):
    conn = get_connection()
    conn.execute(
        "UPDATE items SET name=?,category_id=?,price=?,stock=?,size=? WHERE id=?",
        (name, category_id if category_id else None, price, stock, size, item_id),
    )
    conn.commit()
    conn.close()


def delete_item(item_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def delete_items(item_ids):
    """Bulk delete products."""
    if not item_ids: return
    conn = get_connection()
    try:
        placeholders = ",".join(["?"] * len(item_ids))
        conn.execute(f"DELETE FROM items WHERE id IN ({placeholders})", item_ids)
        conn.commit()
    finally:
        conn.close()


def get_item_by_id(item_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT i.id, i.product_id, i.name, i.price, i.stock, i.size, i.date_added,
                  c.name as category_name, i.category_id
           FROM items i LEFT JOIN categories c ON i.category_id=c.id
           WHERE i.id=?""", (item_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_items(category_id=None, search="", sort_by="date_added", sort_dir="DESC"):
    conn = get_connection()
    try:
        q = """SELECT i.id, i.product_id, i.name, i.price, i.stock, i.size, i.date_added,
                    c.name as category_name, i.category_id
            FROM items i LEFT JOIN categories c ON i.category_id=c.id
            WHERE 1=1"""
        params = []
        if category_id:
            q += " AND i.category_id=?"
            params.append(category_id)
        if search:
            q += " AND (i.name LIKE ? OR i.product_id LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        allowed = {"name": "i.name", "price": "i.price", "stock": "i.stock", "size": "i.size", "date_added": "i.date_added", "category": "c.name"}
        col = allowed.get(sort_by, "i.date_added")
        direction = "ASC" if sort_dir == "ASC" else "DESC"
        q += f" ORDER BY {col} {direction}"
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def export_items_csv(path):
    import csv
    conn = get_connection()
    try:
        items = list_items(sort_by="name", sort_dir="ASC")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Product ID", "Name", "Category", "Size", "Price", "Stock", "Date Added"])
            for it in items:
                w.writerow([it["product_id"], it["name"], it["category_name"] or "", it["size"], it["price"], it["stock"], it["date_added"]])
    finally:
        conn.close()


def _find_header(headers, syns):
    """Fuzzy header matching."""
    for s in syns:
        for h in headers:
            if s.lower() in h.lower():
                return h
    return None


def preview_items_csv(path):
    """
    Reads CSV and returns a list of items and metadata for preview.
    (name, category, price, stock, size, exists)
    """
    import csv
    results = []
    new_categories = set()
    
    conn = get_connection()
    try:
        c = conn.cursor()
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = [h.strip() for h in reader.fieldnames]
            
            # Map headers
            h_name = _find_header(headers, ["Product Name", "Item Name", "Name", "Title"])
            h_cat = _find_header(headers, ["Category", "Department", "Type"])
            h_price = _find_header(headers, ["Selling Price", "Sale Price", "Price", "MSRP"])
            h_stock = _find_header(headers, ["Quantity in Stock", "Stock Level", "Stock", "Qty", "Quantity"])
            h_size = _find_header(headers, ["Size", "Variant"])
            h_id = _find_header(headers, ["SKU", "Product ID", "Barcode", "ID"])

            # Basic validation
            if not h_name: raise ValueError("Could not find a 'Name' or 'Product Name' column in CSV.")
            
            for row in reader:
                name = row.get(h_name, "").strip()
                if not name: continue
                
                cat = row.get(h_cat, "General").strip() or "General"
                size = row.get(h_size, "na").strip() or "na"
                
                try:
                    price = float(row.get(h_price, "0").replace("$", "").replace(",", ""))
                except: price = 0.0
                
                try:
                    stock = int(float(row.get(h_stock, "0"))) 
                except: stock = 0
                
                # Check if exists
                exists = c.execute("SELECT id FROM items WHERE name = ? AND size = ?", (name, size)).fetchone() is not None
                
                # Check if category exists
                cat_exists = c.execute("SELECT id FROM categories WHERE name = ?", (cat,)).fetchone() is not None
                if not cat_exists: new_categories.add(cat)
                
                results.append({
                    "name": name,
                    "category": cat,
                    "price": price,
                    "stock": stock,
                    "size": size,
                    "exists": exists,
                    "pid": row.get(h_id, "")
                })
        
        return results, sorted(list(new_categories))
    finally:
        conn.close()


def import_items_csv(path):
    """
    Import items from CSV with smart matching.
    """
    import csv
    conn = get_connection()
    try:
        c = conn.cursor()
        new_cnt = 0
        upd_cnt = 0
        
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = [h.strip() for h in reader.fieldnames]
            
            # Map headers (same as preview)
            h_name = _find_header(headers, ["Product Name", "Item Name", "Name", "Title"])
            h_cat = _find_header(headers, ["Category", "Department", "Type"])
            h_price = _find_header(headers, ["Selling Price", "Sale Price", "Price", "MSRP"])
            h_stock = _find_header(headers, ["Quantity in Stock", "Stock Level", "Stock", "Qty", "Quantity"])
            h_size = _find_header(headers, ["Size", "Variant"])
            h_id = _find_header(headers, ["SKU", "Product ID", "Barcode", "ID"])

            for row in reader:
                name = row.get(h_name, "").strip()
                if not name: continue
                
                cat_name = row.get(h_cat, "General").strip() or "General"
                size = row.get(h_size, "na").strip() or "na"
                pid = row.get(h_id, f"SKU-{datetime.now().strftime('%M%S%f')}")[:20]
                
                try: price = float(row.get(h_price, "0").replace("$", "").replace(",", ""))
                except: price = 0.0
                try: stock = int(float(row.get(h_stock, "0")))
                except: stock = 0
                
                # 1. Handle Category
                cat_id = None
                if cat_name:
                    existing_cat = c.execute("SELECT id FROM categories WHERE name = ?", (cat_name,)).fetchone()
                    if existing_cat:
                        cat_id = existing_cat["id"]
                    else:
                        c.execute("INSERT INTO categories(name) VALUES(?)", (cat_name,))
                        cat_id = c.lastrowid
                
                # 2. Check if Item already exists by Name AND Size (to allow different stocks for different sizes)
                existing_item = c.execute("SELECT id, stock FROM items WHERE name = ? AND size = ?", (name, size)).fetchone()
                
                if existing_item:
                    # Update existing item: Add stock and update price/category/size
                    new_total_stock = existing_item["stock"] + stock
                    c.execute(
                        "UPDATE items SET category_id = ?, price = ?, stock = ? WHERE id = ?",
                        (cat_id, price, new_total_stock, existing_item["id"])
                    )
                    upd_cnt += 1
                else:
                    # Create new item
                    # Use CSV pid if available, else generate
                    final_pid = row.get(h_id, "").strip()
                    if not final_pid:
                        final_pid = _generate_product_id(conn)
                    
                    c.execute(
                        "INSERT INTO items(product_id, name, category_id, price, stock, size, date_added) VALUES(?,?,?,?,?,?,?)",
                        (final_pid, name, cat_id, price, stock, size, datetime.now().strftime("%Y-%m-%d %H:%M"))
                    )
                    new_cnt += 1
                    
        conn.commit()
        return new_cnt, upd_cnt
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def backup_db(dest_path):
    import shutil
    shutil.copy2(DB_PATH, dest_path)


def restore_db(src_path):
    import shutil
    shutil.copy2(src_path, DB_PATH)


# ---------- sales & invoices ----------
def _generate_invoice_number(conn):
    row = conn.execute("SELECT invoice_number FROM invoices ORDER BY id DESC LIMIT 1").fetchone()
    if row:
        num = int(row["invoice_number"].replace("INV-", "")) + 1
    else:
        num = 1
    return f"INV-{num:06d}"

def record_sale(cart_items, cashier_username, total_amount):
    """
    cart_items: list of dicts with {'id': item_id, 'quantity': qty, 'price': price}
    """
    conn = get_connection()
    try:
        inv_num = _generate_invoice_number(conn)
        dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c = conn.cursor()
        # Insert invoice
        c.execute(
            "INSERT INTO invoices(invoice_number, cashier_username, total_amount, date_created) VALUES(?,?,?,?)",
            (inv_num, cashier_username, total_amount, dt_str)
        )
        invoice_id = c.lastrowid
        
        # Insert items and deduct stock (with stock validation)
        for item in cart_items:
            # Check stock is sufficient before deducting
            row = c.execute("SELECT stock FROM items WHERE id = ?", (item['id'],)).fetchone()
            if row is None:
                raise ValueError(f"Item ID {item['id']} not found.")
            if row["stock"] < item['quantity']:
                raise ValueError(f"Insufficient stock for item '{item.get('name', item['id'])}'. "
                                 f"Available: {row['stock']}, Requested: {item['quantity']}")
            c.execute("UPDATE items SET stock = stock - ? WHERE id = ?", (item['quantity'], item['id']))
            c.execute(
                "INSERT INTO invoice_items(invoice_id, item_id, name_at_sale, size_at_sale, quantity, price_at_sale) VALUES(?,?,?,?,?,?)",
                (invoice_id, item['id'], item.get('name', ''), item.get('size', 'na'), item['quantity'], item['price'])
            )
            
        conn.commit()
        return inv_num, dt_str
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_invoice_full(invoice_number):
    """Retrieve an invoice and all its items including refund data."""
    conn = get_connection()
    inv = conn.execute(
        "SELECT * FROM invoices WHERE invoice_number = ?", 
        (invoice_number,)
    ).fetchone()
    if not inv:
        conn.close()
        return None
        
    items = conn.execute("""
        SELECT ii.id as ii_id, ii.item_id, 
               COALESCE(i.name, ii.name_at_sale) as name, 
               COALESCE(i.size, ii.size_at_sale) as size, 
               ii.quantity, ii.price_at_sale, ii.refunded_quantity 
        FROM invoice_items ii
        LEFT JOIN items i ON ii.item_id = i.id
        WHERE ii.invoice_id = ?
    """, (inv["id"],)).fetchall()
    
    conn.close()
    return {"invoice": dict(inv), "items": [dict(it) for it in items]}


def process_refund(invoice_id, refunds_dict, username):
    """
    Process refunds for an invoice. 
    refunds_dict = {invoice_item_id: quantity_to_refund}
    """
    conn = get_connection()
    try:
        c = conn.cursor()
        total_refund_amount = 0.0
        
        for ii_id, refund_qty in refunds_dict.items():
            if refund_qty <= 0: continue
            
            # get current state of this invoice item
            ii = c.execute("SELECT item_id, quantity, price_at_sale, refunded_quantity FROM invoice_items WHERE id = ?", (ii_id,)).fetchone()
            if not ii: continue
            
            available_to_refund = ii["quantity"] - ii["refunded_quantity"]
            if refund_qty > available_to_refund:
                raise ValueError(f"Cannot refund {refund_qty} for item id {ii['item_id']}, only {available_to_refund} available.")
                
            # Update invoice_items
            c.execute("UPDATE invoice_items SET refunded_quantity = refunded_quantity + ? WHERE id = ?", (refund_qty, ii_id))
            
            # Restock item
            c.execute("UPDATE items SET stock = stock + ? WHERE id = ?", (refund_qty, ii["item_id"]))
            
            total_refund_amount += (refund_qty * ii["price_at_sale"])
            
        # Update invoice total refund amount
        if total_refund_amount > 0:
            c.execute("UPDATE invoices SET refunded_amount = refunded_amount + ? WHERE id = ?", (total_refund_amount, invoice_id))
            
            # Add to audit log manually as we have the connection open
            c.execute(
                "INSERT INTO audit_log(username, action, detail, timestamp) VALUES(?,?,?,?)",
                (username, "PROCESS_REFUND", f"Refunded ${total_refund_amount:.2f} on invoice ID {invoice_id}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
        
        conn.commit()
        return total_refund_amount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ---------- sales analytics ----------
def get_sales_summary(period="today"):
    """Get total revenue and transaction count for a time period."""
    conn = get_connection()
    try:
        if period == "today":
            date_filter = "DATE(date_created) = DATE('now', 'localtime')"
        elif period == "week":
            date_filter = "DATE(date_created) >= DATE('now', 'localtime', '-7 days')"
        elif period == "month":
            date_filter = "DATE(date_created) >= DATE('now', 'localtime', '-30 days')"
        else:
            date_filter = "1=1"  # all time

        row = conn.execute(f"""
            SELECT COALESCE(SUM(total_amount - refunded_amount), 0) as revenue,
                   COUNT(*) as transactions
            FROM invoices WHERE {date_filter}
        """).fetchone()
        return {"revenue": row["revenue"], "transactions": row["transactions"]}
    finally:
        conn.close()


def get_top_selling_items(limit=10):
    """Get best-selling items by total quantity sold."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT COALESCE(i.name, ii.name_at_sale) as name, 
                   COALESCE(i.size, ii.size_at_sale) as size, 
                   i.product_id, SUM(ii.quantity - ii.refunded_quantity) as total_sold,
                   SUM((ii.quantity - ii.refunded_quantity) * ii.price_at_sale) as total_revenue
            FROM invoice_items ii
            LEFT JOIN items i ON ii.item_id = i.id
            GROUP BY COALESCE(i.id, ii.name_at_sale, ii.size_at_sale)
            ORDER BY total_sold DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_worst_selling_items(limit=10):
    """Get items with lowest sales (including zero sales)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.name, i.size, i.product_id, COALESCE(SUM(ii.quantity - ii.refunded_quantity), 0) as total_sold
        FROM items i
        LEFT JOIN invoice_items ii ON i.id = ii.item_id
        GROUP BY i.id
        ORDER BY total_sold ASC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_invoices(limit=20):
    """Get most recent invoices with their sold items."""
    conn = get_connection()
    try:
        invoices = conn.execute("""
            SELECT id, invoice_number, cashier_username, total_amount, date_created
            FROM invoices
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        results = []
        for inv in invoices:
            items = conn.execute("""
                SELECT COALESCE(i.name, ii.name_at_sale) as name, 
                       COALESCE(i.size, ii.size_at_sale) as size, 
                       ii.quantity, ii.refunded_quantity, ii.price_at_sale
                FROM invoice_items ii
                LEFT JOIN items i ON ii.item_id = i.id
                WHERE ii.invoice_id = ?
            """, (inv["id"],)).fetchall()
            
            # calculate actual total after refunds
            row = conn.execute("SELECT refunded_amount FROM invoices WHERE id = ?", (inv["id"],)).fetchone()
            refunded_amount = row["refunded_amount"] if row else 0.0

            results.append({
                "invoice_number": inv["invoice_number"],
                "cashier_username": inv["cashier_username"],
                "total_amount": inv["total_amount"] - refunded_amount,
                "date_created": inv["date_created"],
                "items": [{"name": it["name"], "size": it["size"], "quantity": it["quantity"] - it["refunded_quantity"],
                           "price": it["price_at_sale"]} for it in items if it["quantity"] - it["refunded_quantity"] > 0]
            })
        return results
    finally:
        conn.close()


def get_low_stock_items(threshold=5):
    """Get items with stock below threshold."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT i.product_id, i.name, i.size, i.stock, c.name as category_name
            FROM items i
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE i.stock <= ?
            ORDER BY i.stock ASC
        """, (threshold,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

