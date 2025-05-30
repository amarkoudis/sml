import pymysql

def update_customer_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml'
        )
        
        with conn.cursor() as cursor:
            # First, disable foreign key checks
            cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
            
            # Drop the existing tables in correct order
            cursor.execute('DROP TABLE IF EXISTS event')
            print("Dropped event table")
            
            cursor.execute('DROP TABLE IF EXISTS customer')
            print("Dropped customer table")

            # Create new customer table with correct column names
            cursor.execute('''
                CREATE TABLE customer (
                    customerid INT NOT NULL AUTO_INCREMENT,
                    customername VARCHAR(255) NOT NULL,
                    customeraddress VARCHAR(255) NOT NULL,
                    customerphone VARCHAR(50) NOT NULL,
                    customeremail VARCHAR(100) NOT NULL,
                    contactpersonname VARCHAR(255) NOT NULL,
                    bankid INT DEFAULT NULL,
                    PRIMARY KEY (customerid),
                    CONSTRAINT fk_customer_bank FOREIGN KEY (bankid) 
                    REFERENCES banks (bankid) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            ''')
            print("Created customer table")
            
            # Recreate the event table
            cursor.execute('''
                CREATE TABLE event (
                    EventID INT NOT NULL AUTO_INCREMENT,
                    Customerid INT NOT NULL,
                    EventStart DATETIME NOT NULL,
                    EventDescription TEXT,
                    PRIMARY KEY (EventID),
                    CONSTRAINT event_ibfk_1 FOREIGN KEY (Customerid) 
                    REFERENCES customer (customerid)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            ''')
            print("Created event table")
            
            # Insert sample customers
            sample_customers = [
                ('Test Customer 1', 'Address 1', '1234567890', 'test1@email.com', 'Contact 1', 1),
                ('Test Customer 2', 'Address 2', '0987654321', 'test2@email.com', 'Contact 2', 2),
                ('Test Customer 3', 'Address 3', '5555555555', 'test3@email.com', 'Contact 3', None)
            ]
            
            cursor.executemany('''
                INSERT INTO customer (customername, customeraddress, customerphone, 
                                    customeremail, contactpersonname, bankid)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', sample_customers)
            print("Inserted sample customers")
            
            # Insert sample events
            from datetime import datetime, timedelta
            now = datetime.now()
            sample_events = [
                (1, now + timedelta(days=1), 'Test Event 1'),
                (2, now + timedelta(days=2), 'Test Event 2'),
                (3, now + timedelta(days=3), 'Test Event 3')
            ]
            
            cursor.executemany('''
                INSERT INTO event (Customerid, EventStart, EventDescription)
                VALUES (%s, %s, %s)
            ''', sample_events)
            print("Inserted sample events")
            
            # Re-enable foreign key checks
            cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
            
            conn.commit()
            print("Database update completed successfully")

    except Exception as e:
        print(f"Error updating table: {str(e)}")
        # Make sure to re-enable foreign key checks even if there's an error
        try:
            cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
            conn.commit()
        except:
            pass
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_customer_table() 