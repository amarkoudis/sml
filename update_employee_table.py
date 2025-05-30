import pymysql

def update_employee_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Drop the hourlyrate column
            cursor.execute('''
                ALTER TABLE employee
                DROP COLUMN hourlyrate
            ''')
            
            conn.commit()
            print("Employee table updated successfully!")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_employee_table() 