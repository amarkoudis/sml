import pymysql

def execute_sql():
    conn = None
    try:
        # Connect to the database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check if contribution_settings table already exists
            cursor.execute("SHOW TABLES LIKE 'contribution_settings'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # Create the contribution_settings table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS contribution_settings (
                    setting_id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_name VARCHAR(255) NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL,
                    setting_description TEXT,
                    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """)
                
                # Insert default settings
                default_settings = [
                    ('employer_contribution_percentage', '13.0', 'Percentage of employee cost that the employer contributes'),
                    ('employee_contribution_percentage', '8.0', 'Percentage of employee cost that is deducted from employee'),
                    ('vat_rate_default', '19.0', 'Default VAT rate for invoices and calculations'),
                    ('system_currency', 'EUR', 'Default currency symbol for the system')
                ]
                
                for setting in default_settings:
                    cursor.execute("""
                    INSERT INTO contribution_settings 
                    (setting_name, setting_value, setting_description) 
                    VALUES (%s, %s, %s)
                    """, setting)
                
                conn.commit()
                print("Contribution settings table created and populated successfully!")
            else:
                print("Contribution settings table already exists.")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    execute_sql()