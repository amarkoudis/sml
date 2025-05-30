import pymysql
from config import get_mysql_connection

def initialize_contribution_settings():
    """Initialize the detailed social contribution settings in the database"""
    print("Initializing contribution settings...")
    
    # Connect to the database
    conn, cursor = get_mysql_connection()
    
    if not conn or not cursor:
        print("Failed to connect to the database.")
        return
    
    try:
        # Read the SQL script
        with open('sql/contribution_settings.sql', 'r') as sql_file:
            sql_script = sql_file.read()
            
        # MySQL doesn't support INSERT OR IGNORE, replace with INSERT IGNORE
        sql_script = sql_script.replace('INSERT OR IGNORE', 'INSERT IGNORE')
        
        # Execute each statement separately
        statements = sql_script.split(';')
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        print("Contribution settings initialized successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing contribution settings: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_contribution_settings() 