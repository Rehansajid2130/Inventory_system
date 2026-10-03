# Inventory Management System

A fast, offline desktop Point-of-Sale (POS) and inventory management application built with Python, CustomTkinter, and SQLite. Features automated PDF invoice generation, sales analytics, return & refund workflows, stock tracking, and complete audit logging.

---

## Quick Start

### 1. One-Click Setup (Windows)
Double-click **`RunMe.bat`** in the project directory. It verifies your Python environment, installs dependencies, and launches the app automatically.

### 2. Manual Setup via Terminal
```bash
# Install required packages
pip install -r requirements.txt

# Launch the application
python main.py
```

---

## Default Credentials

| Username | Password | Role | Description |
|:---|:---|:---|:---|
| **admin** | `admin123` | **Admin** | Full system access: inventory, sales analytics, cashier management, database backups |
| **god** | `god@admin2025` | **God** | Emergency maintenance access: ability to reset any user password |

> **Security Note:** Change these default passwords immediately after your first login.

---

## Features

### 🛒 Cashier POS & Checkout
- **Interactive Product Catalog**: Instant search by item name/ID and category filter dropdown.
- **Cart System**: Add items, select sizes (e.g. S, M, L, XL, na), adjust quantities, and view live subtotal & tax totals.
- **PDF Invoice Generation**: Completing a sale automatically reduces stock, records the transaction, and generates a printable itemized PDF receipt saved in `invoices/`.
- **Returns & Refunds**: Look up receipts by invoice number to process full or partial item returns, automatically restocking inventory.

### 📊 Admin Intelligence & Dashboard
- **Sales Analytics**: View revenue summaries and transaction counts for Today, This Week, This Month, and All-Time.
- **Product Insights**: Track Top-Selling items, Worst-Selling items, and Recent Transactions.
- **Low Stock Threshold Alerts**: Automated visual alerts for products with stock below threshold levels.
- **Audit Logging**: Timestamped logging of user actions (logins, sales, edits, deletions, and refunds) with CSV export capability.

### 📦 Inventory & Category Management
- **Item CRUD**: Add, edit, and bulk-delete items with fields: Name, Category, Size, Price, and Stock Quantity.
- **Interactive CSV Import Preview**: Bulk import products with a preview table displaying new items vs stock updates, with automatic category generation.
- **Data Export**: Export inventory items and audit logs directly to CSV files.
- **Backup & Restore**: Create SQLite database snapshots and restore them directly from the admin panel.

### 🎨 Theme & Appearance
- **Light & Dark Mode**: Dynamic theme switcher (Light / Dark / System) with custom-styled tables and UI cards.

---

## Project Structure

```text
inventory1_app/
├── assets/                     # Login graphics and pattern assets
│   ├── desk_pattern.png
│   └── login_bg.png
├── invoices/                   # Generated PDF customer receipts
├── ui/                         # Modular CustomTkinter interface components
│   ├── admin_dashboard.py      # Admin control panel, metrics & catalog management
│   ├── cashier_view.py         # POS cashier terminal & shopping cart
│   ├── import_preview.py       # Batch CSV import preview modal
│   ├── login_screen.py         # Card-based login screen
│   ├── return_dialog.py        # Refund processing & restocking modal
│   └── theme_helper.py         # Light/Dark table styling helper
├── auth.py                     # PBKDF2 password hashing & authentication logic
├── database.py                 # SQLite database schema, queries & analytics
├── inventory.py                # Inventory logic & ReportLab PDF invoice generation
├── inventory.db                # SQLite database file
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── RunMe.bat                   # One-click Windows launcher
├── USER_MANUAL.md              # Detailed end-user manual
└── .gitignore                  # Git ignore rules
```

---

## Dependencies

- **`customtkinter`**: Modern desktop UI framework
- **`reportlab`**: Vector PDF invoice generation
- **`Pillow`**: Image processing & rounded mask rendering for UI assets
- **`sqlite3`**: Built-in transactional database engine
