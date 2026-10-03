"""Thin convenience layer — most logic lives in database.py."""
import database as db


def add(name, category_id, price, stock=0, size='na'):
    return db.add_item(name, category_id, float(price), int(stock), size)


def edit(item_id, name, category_id, price, stock, size='na'):
    db.update_item(item_id, name, category_id, float(price), int(stock), size)


def remove(item_id):
    db.delete_item(item_id)


def remove_multiple(item_ids):
    db.delete_items(item_ids)


def search(category_id=None, query="", sort_by="date_added", sort_dir="DESC"):
    return db.list_items(category_id, query, sort_by, sort_dir)


def export_csv(path):
    db.export_items_csv(path)

def import_csv(path):
    return db.import_items_csv(path)

def checkout(cart_items, cashier_username, total_amount):
    """
    Records sale in db and generates PDF invoice.
    cart_items: list of dicts {'id', 'name', 'quantity', 'price'}
    """
    inv_num, dt_str = db.record_sale(cart_items, cashier_username, total_amount)
    
    # Log the checkout action
    item_summary = ", ".join([f"{item['quantity']}x {item.get('name', 'Item')}" for item in cart_items])
    db.log_action(cashier_username, "CHECKOUT", f"Processed {inv_num} for ${total_amount:.2f} ({item_summary})")
    
    # Generate PDF
    import os
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    filename = f"invoice_{inv_num}.pdf"
    invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")
    os.makedirs(invoices_dir, exist_ok=True)
    filepath = os.path.join(invoices_dir, filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 750, "INVOICE")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Invoice #: {inv_num}")
    c.drawString(50, 700, f"Date: {dt_str}")
    c.drawString(50, 680, f"Cashier: {cashier_username}")
    
    # Table Header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 640, "Item")
    c.drawString(300, 640, "Qty")
    c.drawString(400, 640, "Price")
    c.drawString(500, 640, "Subtotal")
    c.line(50, 630, 550, 630)
    
    # Items
    y = 610
    c.setFont("Helvetica", 12)
    for item in cart_items:
        subtotal = item['quantity'] * item['price']
        display_name = f"{item['name']} ({item.get('size', 'na')})"
        c.drawString(50, y, display_name[:38])
        c.drawString(300, y, str(item['quantity']))
        c.drawString(400, y, f"${item['price']:.2f}")
        c.drawString(500, y, f"${subtotal:.2f}")
        y -= 20
        if y < 100:
            c.showPage()
            y = 750
            # Re-draw table headers on new page
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Item")
            c.drawString(300, y, "Qty")
            c.drawString(400, y, "Price")
            c.drawString(500, y, "Subtotal")
            c.line(50, y - 10, 550, y - 10)
            y -= 30
            c.setFont("Helvetica", 12)
            
    c.line(50, y - 10, 550, y - 10)
    
    # Total
    c.setFont("Helvetica-Bold", 14)
    c.drawString(400, y - 35, "Total:")
    c.drawString(500, y - 35, f"${total_amount:.2f}")
    
    c.save()
    
    # Try to open the PDF
    try:
        os.startfile(filepath)
    except AttributeError:
        # Mac/Linux fallback (though prompt says Windows)
        import subprocess
        subprocess.call(['open' if os.name == 'mac' else 'xdg-open', filepath])
    except Exception:
        pass
        
    return filepath
