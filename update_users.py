import pymysql

def update_users_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml'
        )
        
        with conn.cursor() as cursor:
            # Add columns one by one to handle any that might already exist
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)")
                print("Added email column")
            except:
                print("Email column might already exist")

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'")
                print("Added status column")
            except:
                print("Status column might already exist")

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                print("Added created_at column")
            except:
                print("Created_at column might already exist")

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login DATETIME")
                print("Added last_login column")
            except:
                print("Last_login column might already exist")

            conn.commit()
            print("Table update completed")

    except Exception as e:
        print(f"Error updating table: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_users_table() 