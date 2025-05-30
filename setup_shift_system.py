import os
import sys
from create_employeerole_table import create_employeerole_table
from create_employee_table import create_employee_table
from create_shift_tables import create_shift_tables

def setup_shift_system():
    print("Setting up shift management system...")
    
    # Create tables in the correct order
    print("\n1. Creating employee role table...")
    create_employeerole_table()
    
    print("\n2. Creating employee table...")
    create_employee_table()
    
    print("\n3. Creating shift and employee_shift tables...")
    create_shift_tables()
    
    print("\nShift management system setup completed successfully!")

if __name__ == "__main__":
    setup_shift_system() 