#!/usr/bin/env python3
import pymysql
import os
import sys

def install_schema():
    # Database connection parameters
    # You can modify these or use environment variables
    db_config = {
        'host': 'localhost',
        'user': 'root',  # Replace with your MySQL username
        'password': 'V0sp0r0si968!',  # Replace with your MySQL password
        'database': 'sml',  # Replace with your database name
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.Cursor
    }
    
    try:
        # Connect to MySQL server
        print("Connecting to MySQL server...")
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # Read the SQL file
        print("Reading SQL schema file...")
        with open('database/schema.sql', 'r') as file:
            sql_commands = file.read()
        
        # Split the commands (in case there are multiple statements)
        commands = sql_commands.split(';')
        
        # Execute each command
        print("Executing SQL commands...")
        for command in commands:
            # Skip empty commands
            if command.strip():
                try:
                    cursor.execute(command)
                    print(f"Executed: {command[:50]}...")
                except pymysql.Error as err:
                    print(f"Error executing command: {err}")
                    print(f"Command was: {command}")
        
        # Commit the changes
        conn.commit()
        print("Schema installation completed successfully!")
        
    except pymysql.Error as err:
        print(f"Error: {err}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    print("Starting schema installation...")
    install_schema() 