-- Drop tables if they exist
DROP TABLE IF EXISTS invoice_item;
DROP TABLE IF EXISTS invoice;

-- Create invoice table
CREATE TABLE invoice (
    invoice_id int NOT NULL AUTO_INCREMENT,
    customer_id int NOT NULL,
    event_id int DEFAULT NULL,
    invoice_date datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date datetime DEFAULT NULL,
    invoice_number varchar(100) NOT NULL,
    status enum('Draft','Sent','Paid','Cancelled') NOT NULL DEFAULT 'Draft',
    vat_rate decimal(5,2) NOT NULL DEFAULT '19.00',
    notes text,
    subtotal decimal(10,2) NOT NULL DEFAULT '0.00',
    vat_amount decimal(10,2) NOT NULL DEFAULT '0.00',
    total decimal(10,2) NOT NULL DEFAULT '0.00',
    PRIMARY KEY (invoice_id),
    UNIQUE KEY invoice_number (invoice_number),
    KEY customer_id (customer_id),
    KEY event_id (event_id),
    CONSTRAINT invoice_customer_fk FOREIGN KEY (customer_id) REFERENCES customer (customerid) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT invoice_event_fk FOREIGN KEY (event_id) REFERENCES event (EventID) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create invoice_item table
CREATE TABLE invoice_item (
    item_id int NOT NULL AUTO_INCREMENT,
    invoice_id int NOT NULL,
    description text NOT NULL,
    quantity decimal(10,2) NOT NULL DEFAULT '1.00',
    unit_price decimal(10,2) NOT NULL DEFAULT '0.00',
    total decimal(10,2) NOT NULL DEFAULT '0.00',
    PRIMARY KEY (item_id),
    KEY invoice_id (invoice_id),
    CONSTRAINT invoice_item_invoice_fk FOREIGN KEY (invoice_id) REFERENCES invoice (invoice_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create indexes for better performance
CREATE INDEX idx_invoice_customer ON invoice(customer_id);
CREATE INDEX idx_invoice_event ON invoice(event_id);
CREATE INDEX idx_invoice_date ON invoice(invoice_date);
CREATE INDEX idx_invoice_status ON invoice(status);
CREATE INDEX idx_invoice_number ON invoice(invoice_number);
CREATE INDEX idx_invoice_item_invoice ON invoice_item(invoice_id); 