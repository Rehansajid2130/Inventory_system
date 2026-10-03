# 📋 Inventory Management System — User Manual

Welcome to your new **Inventory Management System**. This guide will show you how to use every part of the app in simple steps.

---

## 🚀 1. Getting Started (One-Click Setup)
The easiest way to start the app is to use the **RunMe.bat** file:
1.  Open the project folder (`inventory1_app`).
2.  Double-click the **RunMe.bat** file.
3.  **What it does**: 
    -   It checks if you have **Python** installed.
    -   If not, it **automatically downloads and installs Python** for you.
    -   It installs all the necessary libraries (`customtkinter`, `reportlab`).
    -   It launches the app automatically via `python main.py`.

Alternatively, via terminal:
```bash
pip install -r requirements.txt
python main.py
```

---

## 🔐 2. Logging In
*   **Username**: Type your assigned name (Default Admin: `admin` / Password: `admin123`).
*   **Password**: Type your secret password.
*   **Admin Mode**: If you are an Admin, you will see all the settings and full management dashboards.
*   **Cashier Mode**: If you are a Cashier, you will go straight to the checkout/selling screen.

---

## 📊 3. Admin Dashboard (For Managers)
The Dashboard is where you control the whole shop. You can switch between these tabs on the left:

### 📈 Sales Dashboard
- See your **Total Revenue** and **Transactions** for Today, This Week, or This Month.
- See which items are **Top Selling** and which are **Low on Stock**.

### 📦 Inventory
- **Add Item**: Click the "+" button to add new products with sizes and stock levels.
- **Edit/Delete**: Select an item in the list to change its price or remove it.
- **CSV Import**: Click "Import CSV" to add many items at once from a file with interactive preview and validation.

### 👥 Users
- Create accounts for your employees. 
- You can set them as **Admin** (controls everything) or **Cashier** (can only sell).

### 💾 Backup & Restore
- **Create Backup**: Save a copy of your database to keep your data safe.
- **Restore**: If you have a problem, you can load an old backup to get your data back.

---

## 🛒 4. Cashier Terminal (For Selling)
This is where the actual selling happens:

1.  **Find Items**: Look at the list on the left side, filter by category or search.
2.  **Add to Cart**: Select an item and click the **➕Add to Cart** button.
3.  **Checkout**: When the customer is ready, click **✅Checkout**. The app automatically prints a PDF invoice and updates your inventory stock.
4.  **Clear Cart**: Click **🗑️Clear** if you want to start over.

---

## ↩️ 5. Handling Returns & Refunds
If a customer brings back an item:
1.  Go to the **Returns** tab or click **Returns** in the Cashier view.
2.  Type the **Invoice Number** (from their receipt, e.g. `INV-000001`).
3.  Choose the item they want to return and click **🔄Refund Selected Item** (or **Refund Entire Invoice**).
4.  The system will automatically restore the product back into your stock and update sales analytics.

---

## 🌙 6. Theme & Settings
You can change the look of the app at any time:
- Use the **Menu** at the bottom left to pick **Light** (White) or **Dark** (Black) mode.
- The tables and cards will automatically adjust!

---

## 📝 7. Audit Log
- Every action (Login, Sales, Edit, Deletion, Refunds) is recorded here with timestamps.
- You can see **who** did **what** and **when**.
- Click **📥Export CSV** to save this list to your computer.
