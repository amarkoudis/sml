import pymysql

def check_company_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check company table structure
            cursor.execute("DESCRIBE company")
            columns = cursor.fetchall()
            print("\nCompany table structure:")
            for col in columns:
                print(col)
            
            # Count records
            cursor.execute("SELECT COUNT(*) as count FROM company")
            count = cursor.fetchone()['count']
            print(f"\nNumber of companies: {count}")
            
            # Sample data
            if count > 0:
                cursor.execute("SELECT * FROM company LIMIT 1")
                sample = cursor.fetchone()
                print("\nSample company data:")
                for key, value in sample.items():
                    print(f"{key}: {value}")
                    
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_company_table() 