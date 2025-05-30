import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

def check_and_create_admin():
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml'
        )
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # First, check if user exists
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            user = cursor.fetchone()
            
            if user:
                print("Existing admin user found:")
                print(f"ID: {user['id']}")
                print(f"Username: {user['username']}")
                print("Deleting existing admin user...")
                cursor.execute("DELETE FROM users WHERE username = 'admin'")
                connection.commit()
            
            # Create new admin user
            username = 'admin'
            password = 'admin123'
            hashed_password = generate_password_hash(password, method='sha256')
            
            cursor.execute('''
                INSERT INTO users (username, password, email, role)
                VALUES (%s, %s, %s, %s)
            ''', (username, hashed_password, 'admin@example.com', 'admin'))
            
            connection.commit()
            print("\nNew admin user created successfully!")
            print(f"Username: {username}")
            print(f"Password: {password}")
            
            # Verify the password
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            new_user = cursor.fetchone()
            if check_password_hash(new_user['password'], 'admin123'):
                print("\nPassword verification successful!")
            else:
                print("\nPassword verification failed!")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        connection.close()

if __name__ == "__main__":
    check_and_create_admin() 