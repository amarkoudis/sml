import pymysql
from werkzeug.security import generate_password_hash

def setup_database():
    try:
        # First connect without database to create it
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS sml")
            cursor.execute("USE sml")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Check if admin user exists
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin_exists = cursor.fetchone()
            
            if not admin_exists:
                # Create default admin user
                hashed_password = generate_password_hash('admin123')
                cursor.execute("""
                    INSERT INTO users (username, password, email, role)
                    VALUES (%s, %s, %s, %s)
                """, ('admin', hashed_password, 'admin@example.com', 'admin'))
                print("Created default admin user (username: admin, password: admin123)")
            
            connection.commit()
            print("Database and tables created successfully!")
            
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False
    finally:
        connection.close()
    
    return True

if __name__ == "__main__":
    setup_database() 