from datetime import datetime

class Invoice:
    def __init__(self, invoice_id=None, customer_id=None, event_id=None, invoice_date=None, 
                 due_date=None, invoice_number=None, status="Draft", vat_rate=19.0, 
                 notes=None, subtotal=0.0, vat_amount=0.0, total=0.0):
        self.invoice_id = invoice_id
        self.customer_id = customer_id
        self.event_id = event_id
        self.invoice_date = invoice_date or datetime.now()
        self.due_date = due_date
        self.invoice_number = invoice_number
        self.status = status
        self.vat_rate = vat_rate
        self.notes = notes
        self.subtotal = subtotal
        self.vat_amount = vat_amount
        self.total = total
        self.items = []
        
    def add_item(self, item):
        self.items.append(item)
        
    def calculate_totals(self):
        self.subtotal = sum(item.total for item in self.items)
        self.vat_amount = self.subtotal * (self.vat_rate / 100)
        self.total = self.subtotal + self.vat_amount
        
    @staticmethod
    def from_dict(data):
        invoice = Invoice(
            invoice_id=data.get('invoice_id'),
            customer_id=data.get('customer_id'),
            event_id=data.get('event_id'),
            invoice_date=data.get('invoice_date'),
            due_date=data.get('due_date'),
            invoice_number=data.get('invoice_number'),
            status=data.get('status', 'Draft'),
            vat_rate=data.get('vat_rate', 19.0),
            notes=data.get('notes'),
            subtotal=data.get('subtotal', 0.0),
            vat_amount=data.get('vat_amount', 0.0),
            total=data.get('total', 0.0)
        )
        if 'items' in data:
            for item_data in data['items']:
                invoice.add_item(InvoiceItem.from_dict(item_data))
        return invoice
    
    def to_dict(self):
        return {
            'invoice_id': self.invoice_id,
            'customer_id': self.customer_id,
            'event_id': self.event_id,
            'invoice_date': self.invoice_date,
            'due_date': self.due_date,
            'invoice_number': self.invoice_number,
            'status': self.status,
            'vat_rate': self.vat_rate,
            'notes': self.notes,
            'subtotal': self.subtotal,
            'vat_amount': self.vat_amount,
            'total': self.total,
            'items': [item.to_dict() for item in self.items]
        }

class InvoiceItem:
    def __init__(self, item_id=None, invoice_id=None, description=None, quantity=1, 
                 unit_price=0.0, total=0.0):
        self.item_id = item_id
        self.invoice_id = invoice_id
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.total = total or (quantity * unit_price)
        
    def calculate_total(self):
        self.total = self.quantity * self.unit_price
        
    @staticmethod
    def from_dict(data):
        return InvoiceItem(
            item_id=data.get('item_id'),
            invoice_id=data.get('invoice_id'),
            description=data.get('description'),
            quantity=data.get('quantity', 1),
            unit_price=data.get('unit_price', 0.0),
            total=data.get('total', 0.0)
        )
        
    def to_dict(self):
        return {
            'item_id': self.item_id,
            'invoice_id': self.invoice_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total': self.total
        } 