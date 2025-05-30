import pymysql

def check_tables():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check event table structure
            cursor.execute("DESCRIBE event")
            event_columns = cursor.fetchall()
            print("\nEvent table structure:")
            for col in event_columns:
                print(col)
            
            # Check customer table structure
            cursor.execute("DESCRIBE customer")
            customer_columns = cursor.fetchall()
            print("\nCustomer table structure:")
            for col in customer_columns:
                print(col)
            
            # Count records in both tables
            cursor.execute("SELECT COUNT(*) as count FROM event")
            event_count = cursor.fetchone()['count']
            print(f"\nNumber of events: {event_count}")
            
            cursor.execute("SELECT COUNT(*) as count FROM customer")
            customer_count = cursor.fetchone()['count']
            print(f"Number of customers: {customer_count}")
            
            # Sample data from event table
            if event_count > 0:
                print("\nSample event data:")
                cursor.execute("SELECT * FROM event LIMIT 1")
                sample_event = cursor.fetchone()
                for key, value in sample_event.items():
                    print(f"{key}: {value}")
                    
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_tables() 