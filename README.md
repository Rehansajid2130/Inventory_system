# Inventory Manager — Cloth & Jewelry Shop

A fast, offline desktop inventory management system built with Python, CustomTkinter, and SQLite.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Default Credentials

| Username | Password        | Role  |
|----------|-----------------|-------|
| admin    | admin123        | Admin |
| god      | god@admin2025   | God   |

**Change these passwords immediately after first login.**

## Features

- **Checkout & Invoice**: Cashier builds a shopping cart, completes a sale, and generates a printable PDF invoice with itemized products, prices, and totals
- **Sales Dashboard**: Admin can view revenue summaries (today/week/month/all time), top-selling items, worst-selling items, recent transactions, and low stock alerts
- **Stock Management**: Track inventory quantities — stock is automatically deducted on checkout with safeguards against overselling
- **Inventory**: Add, edit, delete, search, sort, filter items by category
- **Categories**: Create, edit, delete categories
- **Users**: Admin can create/delete cashier accounts
- **Roles**: Admin (full access), Cashier (checkout & view), God (emergency recovery)
- **Export**: CSV export of inventory (includes stock levels)
- **Backup/Restore**: Full database backup and restore
- **Security**: PBKDF2-hashed passwords, role-based access, stock validation in transactions

## Project Structure

```
main.py              → App entry point
database.py          → SQLite operations & analytics queries
auth.py              → Authentication & password hashing
inventory.py         → Inventory logic layer & PDF invoice generation
invoices/            → Generated PDF invoices saved here
ui/
  login_screen.py    → Login UI
  admin_dashboard.py → Admin panel with sales dashboard
  cashier_view.py    → Cashier checkout with cart system
```

## Dependencies

- `customtkinter` — Modern UI framework
- `reportlab` — PDF invoice generation
