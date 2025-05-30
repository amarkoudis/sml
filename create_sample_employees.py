import pymysql

def create_sample_employees():
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
            # First, check if we have employee roles
            cursor.execute("SELECT COUNT(*) as count FROM employeerole")
            role_count = cursor.fetchone()['count']
            
            # If no roles exist, create some basic roles
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
            
            # Get the role IDs
            cursor.execute("SELECT employeeroleid, employeerolename FROM employeerole")
            roles = cursor.fetchall()
            role_map = {role['employeerolename']: role['employeeroleid'] for role in roles}
            
            # Check if we have a company to associate with employees
            cursor.execute("SELECT COUNT(*) as count FROM company")
            company_count = cursor.fetchone()['count']
            
            if company_count == 0:
                print("Creating a sample company...")
                cursor.execute(
                    "INSERT INTO company (companyname, bankid, transactiontype) VALUES (%s, %s, %s)",
                    ("Sample Company", 1, 'S')
                )
                conn.commit()
                print("Created sample company")
            
            # Get a company ID
            cursor.execute("SELECT companyid FROM company LIMIT 1")
            company_id = cursor.fetchone()['companyid']
            
            # Check if we have a bank to associate with employees
            cursor.execute("SELECT COUNT(*) as count FROM banks")
            bank_count = cursor.fetchone()['count']
            
            if bank_count == 0:
                print("Creating a sample bank...")
                cursor.execute(
                    "INSERT INTO banks (bankname, bankcode) VALUES (%s, %s)",
                    ("Sample Bank", "SMPL")
                )
                conn.commit()
                print("Created sample bank")
            
            # Get a bank ID
            cursor.execute("SELECT bankid FROM banks LIMIT 1")
            bank_id = cursor.fetchone()['bankid']
            
            # Create sample employees
            print("Creating sample employees...")
            
            # Sample employees data
            employees = [
                # Format: (employeename, email, tel, employeeroleid, gender, costperhour, chargeperhour, status)
                ("John Smith", "john.smith@example.com", "1234567890", role_map.get('Waiter', 1), "Male", 15.00, 25.00, "Active"),
                ("Jane Doe", "jane.doe@example.com", "0987654321", role_map.get('Bartender', 2), "Female", 18.00, 30.00, "Active"),
                ("Michael Johnson", "michael.johnson@example.com", "5551234567", role_map.get('Manager', 3), "Male", 25.00, 40.00, "Active"),
                ("Sarah Williams", "sarah.williams@example.com", "5559876543", role_map.get('Chef', 4), "Female", 22.00, 35.00, "Active"),
                ("David Brown", "david.brown@example.com", "5555555555", role_map.get('Waiter', 1), "Male", 15.00, 25.00, "Active"),
                ("Emily Davis", "emily.davis@example.com", "5551112222", role_map.get('Bartender', 2), "Female", 18.00, 30.00, "Active"),
                ("Robert Miller", "robert.miller@example.com", "5553334444", role_map.get('Waiter', 1), "Male", 15.00, 25.00, "Active"),
                ("Jennifer Wilson", "jennifer.wilson@example.com", "5556667777", role_map.get('Bartender', 2), "Female", 18.00, 30.00, "Active"),
                ("William Moore", "william.moore@example.com", "5558889999", role_map.get('Chef', 4), "Male", 22.00, 35.00, "Active"),
                ("Elizabeth Taylor", "elizabeth.taylor@example.com", "5550001111", role_map.get('Manager', 3), "Female", 25.00, 40.00, "Active")
            ]
            
            # Insert employees
            for employee in employees:
                cursor.execute("""
                    INSERT INTO employee (
                        employeename, email, tel, employeeroleid, 
                        gender, costperhour, chargeperhour, status, 
                        companyid, bankid, swiftno, address, city, 
                        age, nationality, passportid, EmploymentAgreement, 
                        employeeidno, transactiontype
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    employee[0],  # employeename
                    employee[1],  # email
                    employee[2],  # tel
                    employee[3],  # employeeroleid
                    employee[4],  # gender
                    employee[5],  # costperhour
                    employee[6],  # chargeperhour
                    employee[7],  # status
                    company_id,   # companyid
                    bank_id,      # bankid
                    "SMPL123456", # swiftno
                    "123 Main St", # address
                    "Nicosia",    # city
                    30,           # age
                    "Cypriot",    # nationality
                    "P123456",    # passportid
                    "Agreement",  # EmploymentAgreement
                    1000 + employees.index(employee),  # employeeidno
                    'S'           # transactiontype
                ))
            
            conn.commit()
            print(f"Created {len(employees)} sample employees")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_sample_employees() 