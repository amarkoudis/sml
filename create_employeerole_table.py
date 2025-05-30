import pymysql

def create_employeerole_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Create employeerole table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employeerole (
                    employeeroleid INT NOT NULL AUTO_INCREMENT,
                    employeerolename VARCHAR(255) NOT NULL,
                    PRIMARY KEY (employeeroleid)
                )
            ''')
            
            conn.commit()
            print("Employee Role table created successfully!")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_employeerole_table() 