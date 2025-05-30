import pymysql

def add_total_hours_column():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check if column exists
            cursor.execute("SHOW COLUMNS FROM shifts LIKE 'total_hours'")
            if not cursor.fetchone():
                # Add total_hours column
                cursor.execute('''
                    ALTER TABLE shifts 
                    ADD COLUMN total_hours DECIMAL(10,2) DEFAULT 0
                ''')
            
            # Calculate and update total hours for existing shifts
            cursor.execute('''
                UPDATE shifts s
                SET total_hours = (
                    SELECT COALESCE(SUM(es.hours), 0)
                    FROM employee_shifts es
                    WHERE es.shiftid = s.shiftid
                )
            ''')
            
            conn.commit()
            print("Successfully added total_hours column and updated existing data")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_total_hours_column() 