import pymysql
import traceback
import datetime

def main():
    conn = None
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Connected successfully!")
        
        with conn.cursor() as cursor:
            # Check if employee table exists
            print("Checking employee table...")
            cursor.execute("SHOW TABLES LIKE 'employee'")
            if not cursor.fetchone():
                print("Employee table doesn't exist!")
                return
            
            # Get employee table structure
            cursor.execute("DESCRIBE employee")
            employee_structure = cursor.fetchall()
            field_names = [field['Field'] for field in employee_structure]
            required_fields = []
            
            print("\nEmployee table columns:")
            for field in employee_structure:
                is_required = "Required" if field['Null'] == 'NO' and field['Default'] is None and field['Extra'] != 'auto_increment' else "Optional"
                if field['Null'] == 'NO' and field['Default'] is None and field['Extra'] != 'auto_increment':
                    required_fields.append(field['Field'])
                print(f"{field['Field']}: {field['Type']} ({is_required}, Default: {field['Default']})")
            
            print(f"\nRequired fields for insertion: {', '.join(required_fields)}")
            
            # Count employees
            cursor.execute("SELECT COUNT(*) as count FROM employee")
            count = cursor.fetchone()['count']
            print(f"\nFound {count} employees in the database")
            
            # Display all employees
            print("\nListing all employees:")
            cursor.execute('''
                SELECT e.*, er.employeerolename 
                FROM employee e 
                LEFT JOIN employeerole er ON e.employeeroleid = er.employeeroleid
            ''')
            employees = cursor.fetchall()
            
            if len(employees) > 0:
                for i, employee in enumerate(employees, 1):
                    print(f"\nEmployee #{i}:")
                    print(f"ID: {employee['employeeid']}")
                    print(f"Name: {employee['employeename']}")
                    print(f"Role: {employee.get('employeerolename', 'Not assigned')}")
                    print(f"Email: {employee.get('email', 'N/A')}")
                    print(f"Phone: {employee.get('tel', 'N/A')}")
                    print(f"Gender: {employee.get('gender', 'N/A')}")
                    print(f"Status: {employee.get('status', 'N/A')}")
                    print(f"Hourly Rate: £{employee.get('chargeperhour', 0)}")
            else:
                print("No employees found in the database")
                
                # Create sample employees
                create_sample = input("\nWould you like to create sample employees? (y/n): ")
                if create_sample.lower() != 'y':
                    return
                
                print("\nInserting sample employees...")
                
                # First ensure we have employee roles
                cursor.execute("SELECT COUNT(*) as count FROM employeerole")
                role_count = cursor.fetchone()['count']
                
                if role_count == 0:
                    print("Creating employee roles...")
                    roles = [
                        ('Waiter',),
                        ('Bartender',),
                        ('Manager',),
                        ('Chef',)
                    ]
                    cursor.executemany(
                        "INSERT INTO employeerole (employeerolename) VALUES (%s)",
                        roles
                    )
                    conn.commit()
                    print(f"Created {len(roles)} employee roles")
                
                # Get role IDs
                cursor.execute("SELECT employeeroleid, employeerolename FROM employeerole")
                roles = cursor.fetchall()
                role_map = {role['employeerolename']: role['employeeroleid'] for role in roles}
                
                # Check if we have companies
                cursor.execute("SELECT COUNT(*) as count FROM company")
                company_count = cursor.fetchone()['count']
                
                company_id = None
                bank_id = None
                
                if company_count == 0:
                    print("Creating a sample company...")
                    # Check if we have banks
                    cursor.execute("SELECT COUNT(*) as count FROM banks")
                    bank_count = cursor.fetchone()['count']
                    
                    if bank_count == 0:
                        print("Creating a sample bank...")
                        cursor.execute(
                            "INSERT INTO banks (bankname, biccode) VALUES (%s, %s)",
                            ("Sample Bank", "SAMPLECODE")
                        )
                        conn.commit()
                        bank_id = cursor.lastrowid
                        print("Created sample bank with ID:", bank_id)
                    else:
                        cursor.execute("SELECT bankid FROM banks LIMIT 1")
                        bank_id = cursor.fetchone()['bankid']
                    
                    cursor.execute(
                        "INSERT INTO company (companyname, bankid, transactiontype) VALUES (%s, %s, %s)",
                        ("Sample Company", bank_id, 'S')
                    )
                    conn.commit()
                    company_id = cursor.lastrowid
                    print("Created sample company with ID:", company_id)
                else:
                    cursor.execute("SELECT companyid FROM company LIMIT 1")
                    company_id = cursor.fetchone()['companyid']
                    
                    cursor.execute("SELECT bankid FROM banks LIMIT 1")
                    bank_id = cursor.fetchone()['bankid']
                
                # Build employee objects based on required fields
                print(f"Using company_id: {company_id}, bank_id: {bank_id}")
                
                # Sample employee data
                employees = [
                    {
                        'employeename': 'John Doe',
                        'email': 'john@example.com',
                        'tel': '1234567890',
                        'employeeroleid': role_map.get('Waiter', 1),
                        'gender': 'Male',
                        'costperhour': 15.00,
                        'chargeperhour': 25.00,
                        'status': 'Active',
                        'companyid': company_id,
                        'bankid': bank_id,
                        'swiftno': 'SWIFT123',
                        'address': '123 Main St',
                        'city': 'Nicosia',
                        'age': 30,
                        'nationality': 'Cypriot',
                        'passportid': 'PASS123',
                        'EmploymentAgreement': 'Standard',
                        'employeeidno': 1001,
                        'phone': '1234567890'
                    },
                    {
                        'employeename': 'Jane Smith',
                        'email': 'jane@example.com',
                        'tel': '0987654321',
                        'employeeroleid': role_map.get('Bartender', 2),
                        'gender': 'Female',
                        'costperhour': 18.00,
                        'chargeperhour': 28.00,
                        'status': 'Active',
                        'companyid': company_id,
                        'bankid': bank_id,
                        'swiftno': 'SWIFT456',
                        'address': '456 Oak St',
                        'city': 'Limassol',
                        'age': 25,
                        'nationality': 'EU',
                        'passportid': 'PASS456',
                        'EmploymentAgreement': 'Standard',
                        'employeeidno': 1002,
                        'phone': '0987654321'
                    }
                ]
                
                # Check for missing required fields
                for employee in employees:
                    for required_field in required_fields:
                        if required_field not in employee:
                            print(f"Warning: Required field {required_field} is missing from employee data")
                
                # Prepare and execute insertions
                for employee in employees:
                    columns = ', '.join(employee.keys())
                    placeholders = ', '.join(['%s'] * len(employee))
                    sql = f"INSERT INTO employee ({columns}) VALUES ({placeholders})"
                    
                    try:
                        print(f"Executing SQL: {sql}")
                        print(f"Values: {list(employee.values())}")
                        cursor.execute(sql, list(employee.values()))
                        conn.commit()
                        print(f"Successfully inserted employee: {employee['employeename']}")
                    except Exception as e:
                        print(f"Error inserting employee {employee['employeename']}: {str(e)}")
                        traceback.print_exc()
                        conn.rollback()
            
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
    finally:
        if conn and conn.open:
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    main() 