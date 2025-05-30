import pymysql
from datetime import datetime
from models.invoice import Invoice, InvoiceItem

def create_invoice(invoice):
    """Create a new invoice in the database"""
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Insert invoice record
            sql = """
            INSERT INTO invoice (
                customer_id, event_id, invoice_date, due_date, 
                invoice_number, status, vat_rate, notes, 
                subtotal, vat_amount, total
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            cursor.execute(sql, (
                invoice.customer_id, invoice.event_id, invoice.invoice_date, invoice.due_date,
                invoice.invoice_number, invoice.status, invoice.vat_rate, invoice.notes,
                invoice.subtotal, invoice.vat_amount, invoice.total
            ))
            
            # Get the generated invoice ID
            invoice_id = conn.insert_id()
            invoice.invoice_id = invoice_id
            
            # Insert invoice items
            if invoice.items:
                for item in invoice.items:
                    item.invoice_id = invoice_id
                    sql = """
                    INSERT INTO invoice_item (
                        invoice_id, description, quantity, unit_price, total
                    ) VALUES (
                        %s, %s, %s, %s, %s
                    )
                    """
                    cursor.execute(sql, (
                        item.invoice_id, item.description, item.quantity, 
                        item.unit_price, item.total
                    ))
            
            conn.commit()
            return invoice_id
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating invoice: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_invoice(invoice_id):
    """Get an invoice by ID with all its items"""
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get invoice
            sql = "SELECT * FROM invoice WHERE invoice_id = %s"
            cursor.execute(sql, (invoice_id,))
            invoice_data = cursor.fetchone()
            
            if not invoice_data:
                return None
                
            # Get invoice items
            sql = "SELECT * FROM invoice_item WHERE invoice_id = %s"
            cursor.execute(sql, (invoice_id,))
            items_data = cursor.fetchall()
            
            # Create invoice object
            invoice = Invoice(
                invoice_id=invoice_data['invoice_id'],
                customer_id=invoice_data['customer_id'],
                event_id=invoice_data['event_id'],
                invoice_date=invoice_data['invoice_date'],
                due_date=invoice_data['due_date'],
                invoice_number=invoice_data['invoice_number'],
                status=invoice_data['status'],
                vat_rate=float(invoice_data['vat_rate']),
                notes=invoice_data['notes'],
                subtotal=float(invoice_data['subtotal']),
                vat_amount=float(invoice_data['vat_amount']),
                total=float(invoice_data['total'])
            )
            
            # Add items to invoice
            for item_data in items_data:
                item = InvoiceItem(
                    item_id=item_data['item_id'],
                    invoice_id=item_data['invoice_id'],
                    description=item_data['description'],
                    quantity=float(item_data['quantity']),
                    unit_price=float(item_data['unit_price']),
                    total=float(item_data['total'])
                )
                invoice.add_item(item)
                
            return invoice
            
    except Exception as e:
        print(f"Error retrieving invoice: {e}")
        raise
    finally:
        if conn:
            conn.close()

def update_invoice(invoice):
    """Update an existing invoice"""
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Update invoice record
            sql = """
            UPDATE invoice SET
                customer_id = %s, event_id = %s, invoice_date = %s, due_date = %s,
                invoice_number = %s, status = %s, vat_rate = %s, notes = %s,
                subtotal = %s, vat_amount = %s, total = %s
            WHERE invoice_id = %s
            """
            cursor.execute(sql, (
                invoice.customer_id, invoice.event_id, invoice.invoice_date, invoice.due_date,
                invoice.invoice_number, invoice.status, invoice.vat_rate, invoice.notes,
                invoice.subtotal, invoice.vat_amount, invoice.total, invoice.invoice_id
            ))
            
            # Delete existing invoice items
            sql = "DELETE FROM invoice_item WHERE invoice_id = %s"
            cursor.execute(sql, (invoice.invoice_id,))
            
            # Insert updated invoice items
            if invoice.items:
                for item in invoice.items:
                    sql = """
                    INSERT INTO invoice_item (
                        invoice_id, description, quantity, unit_price, total
                    ) VALUES (
                        %s, %s, %s, %s, %s
                    )
                    """
                    cursor.execute(sql, (
                        invoice.invoice_id, item.description, item.quantity, 
                        item.unit_price, item.total
                    ))
            
            conn.commit()
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error updating invoice: {e}")
        raise
    finally:
        if conn:
            conn.close()

def delete_invoice(invoice_id):
    """Delete an invoice and all its items"""
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Delete invoice items first (due to foreign key constraint)
            sql = "DELETE FROM invoice_item WHERE invoice_id = %s"
            cursor.execute(sql, (invoice_id,))
            
            # Delete invoice
            sql = "DELETE FROM invoice WHERE invoice_id = %s"
            cursor.execute(sql, (invoice_id,))
            
            conn.commit()
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error deleting invoice: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_all_invoices():
    """Get all invoices with basic information (without items)"""
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get all invoices
            sql = """
            SELECT i.*, c.customername 
            FROM invoice i
            LEFT JOIN customer c ON i.customer_id = c.customerid
            ORDER BY i.invoice_date DESC
            """
            cursor.execute(sql)
            invoices_data = cursor.fetchall()
            
            invoices = []
            for invoice_data in invoices_data:
                invoice = Invoice(
                    invoice_id=invoice_data['invoice_id'],
                    customer_id=invoice_data['customer_id'],
                    event_id=invoice_data['event_id'],
                    invoice_date=invoice_data['invoice_date'],
                    due_date=invoice_data['due_date'],
                    invoice_number=invoice_data['invoice_number'],
                    status=invoice_data['status'],
                    vat_rate=float(invoice_data['vat_rate']),
                    notes=invoice_data['notes'],
                    subtotal=float(invoice_data['subtotal']),
                    vat_amount=float(invoice_data['vat_amount']),
                    total=float(invoice_data['total'])
                )
                # Add customer name to invoice object
                invoice.customer_name = invoice_data.get('customername', 'Unknown')
                invoices.append(invoice)
                
            return invoices
            
    except Exception as e:
        print(f"Error retrieving invoices: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_invoices_by_event_id(event_id):
    """Get all invoices for a specific event"""
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Get invoices for the event
            sql = """
            SELECT i.*, c.customername 
            FROM invoice i
            LEFT JOIN customer c ON i.customer_id = c.customerid
            WHERE i.event_id = %s
            ORDER BY i.invoice_date DESC
            """
            cursor.execute(sql, (event_id,))
            invoices_data = cursor.fetchall()
            
            invoices = []
            for invoice_data in invoices_data:
                invoice = Invoice(
                    invoice_id=invoice_data['invoice_id'],
                    customer_id=invoice_data['customer_id'],
                    event_id=invoice_data['event_id'],
                    invoice_date=invoice_data['invoice_date'],
                    due_date=invoice_data['due_date'],
                    invoice_number=invoice_data['invoice_number'],
                    status=invoice_data['status'],
                    vat_rate=float(invoice_data['vat_rate']),
                    notes=invoice_data['notes'],
                    subtotal=float(invoice_data['subtotal']),
                    vat_amount=float(invoice_data['vat_amount']),
                    total=float(invoice_data['total'])
                )
                # Add customer name to invoice object
                invoice.customer_name = invoice_data.get('customername', 'Unknown')
                invoices.append(invoice)
                
            return invoices
            
    except Exception as e:
        print(f"Error retrieving invoices for event: {e}")
        raise
    finally:
        if conn:
            conn.close()

def generate_invoice_number():
    """Generate a unique invoice number based on the current date and a sequential number"""
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        # Format: INV-YYYYMMDD-XXXX where XXXX is a sequential number
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"INV-{today}-"
        
        with conn.cursor() as cursor:
            sql = """
            SELECT MAX(invoice_number) as last_invoice 
            FROM invoice 
            WHERE invoice_number LIKE %s
            """
            cursor.execute(sql, (f"{prefix}%",))
            result = cursor.fetchone()
            
            if result and result['last_invoice']:
                # Extract the sequence number from the last invoice number
                last_num = int(result['last_invoice'].split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
                
            # Format with leading zeros
            return f"{prefix}{new_num:04d}"
            
    except Exception as e:
        print(f"Error generating invoice number: {e}")
        raise
    finally:
        if conn:
            conn.close() 