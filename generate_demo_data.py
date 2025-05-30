import pymysql
from datetime import datetime, timedelta
import random
from decimal import Decimal

def connect_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def generate_demo_data():
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            # Temporarily disable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # Clear existing data in reverse order of dependencies
            tables = [
                'employee_shifts',
                'shifts',
                'event',
                'employee',
                'customer',
                'company',
                'banks'
            ]
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            # Generate Banks
            banks = [
                ("Bank of Cyprus", "BCYPCY2N"),
                ("Hellenic Bank", "HEBACY2N"),
                ("Alpha Bank Cyprus", "ABKLCY2N"),
                ("Eurobank Cyprus", "ERBKCY2N")
            ]
            cursor.executemany(
                "INSERT INTO banks (bankname, biccode) VALUES (%s, %s)",
                banks
            )
            print("Generated demo banks")

            # Generate Companies
            companies = [
                ("Cyprus Staffing Solutions Ltd", "CY123456789", 1, 'S'),
                ("Event Staff Pro", "CY987654321", 2, 'S'),
                ("Hospitality Team Cyprus", "CY456789123", 3, 'B')
            ]
            cursor.executemany(
                "INSERT INTO company (companyname, companydebitaccount, bankid, transactiontype) VALUES (%s, %s, %s, %s)",
                companies
            )
            print("Generated demo companies")

            # Generate Customers
            customers = [
                ("Hilton Cyprus", "22 Arch. Makarios III Avenue", "+35722377777", "events@hilton.com.cy", "Maria Georgiou", 1),
                ("Four Seasons Hotel", "67-69 Amathus Avenue", "+35725858000", "events@fourseasons.com.cy", "Andreas Dimitriou", 2),
                ("Columbia Beach Resort", "Pissouri Bay", "+35725833000", "events@columbia-hotels.com", "Elena Papadopoulou", 3),
                ("Parklane Resort", "11 Giannou Kranidioti Street", "+35725862000", "events@parklane.com.cy", "Christos Andreou", 1)
            ]
            cursor.executemany(
                "INSERT INTO customer (customername, customeraddress, customerphone, customeremail, contactpersonname, bankid) VALUES (%s, %s, %s, %s, %s, %s)",
                customers
            )
            print("Generated demo customers")

            # Generate Employees
            cities = ['Nicosia', 'Limassol', 'Larnaca', 'Paphos', 'Famagusta']
            genders = ['Male', 'Female']
            nationalities = ['Cypriot', 'EU', 'Foreigner']
            yes_no = ['Yes', 'No']
            ratings = ['1', '2', '3', '4', '5']
            contact_methods = ['email', 'sms']

            employees = []
            for i in range(20):
                gender = random.choice(genders)
                first_name = "Maria" if gender == "Female" else "Andreas"
                last_name = f"Employee{i+1}"
                
                employee = (
                    'S',  # transactiontype
                    f"{first_name} {last_name}",  # employeename
                    random.randint(1, 3),  # companyid
                    random.randint(1, 4),  # bankid
                    f"SW{str(i+1).zfill(8)}",  # swiftno
                    "EUR",  # currency
                    f"{random.randint(1, 100)} Main Street",  # address
                    "Apt " + str(random.randint(1, 50)),  # address2
                    f"{random.randint(1000, 9999)}",  # zipcode
                    random.choice(cities),  # city
                    random.randint(20, 45),  # age
                    gender,  # gender
                    f"+357{random.randint(95000000, 99999999)}",  # tel
                    random.choice(nationalities),  # nationality
                    f"{first_name.lower()}.{last_name.lower()}@email.com",  # email
                    random.choice(yes_no),  # currentworkplace
                    f"SI{str(random.randint(1000, 9999))}",  # SocialInsuranceno
                    random.choice(yes_no),  # Tattoo
                    random.choice(yes_no),  # AgreementStatus
                    'No',  # CriminalRecordStatus
                    random.choice(yes_no),  # TrainingStatus
                    random.choice(yes_no),  # Interestforfulltime
                    random.choice(yes_no),  # Repeater
                    Decimal(str(random.uniform(8.0, 15.0))).quantize(Decimal('0.00')),  # costperhour
                    Decimal(str(random.uniform(15.0, 25.0))).quantize(Decimal('0.00')),  # chargeperhour
                    'Active',  # status
                    f"P{str(random.randint(100000, 999999))}",  # passportid
                    f"EA{str(random.randint(1000, 9999))}",  # EmploymentAgreement
                    i + 1000,  # employeeidno
                    random.randint(1, 4),  # employeeroleid
                    random.choice(ratings),  # employeeenglishrating
                    random.choice(ratings),  # employeeExperienceRating
                    random.choice(contact_methods)  # contactmethod
                )
                employees.append(employee)

            cursor.executemany("""
                INSERT INTO employee (
                    transactiontype, employeename, companyid, bankid, swiftno, currency,
                    address, address2, zipcode, city, age, gender, tel, nationality,
                    email, currentworkplace, SocialInsuranceno, Tattoo, AgreementStatus,
                    CriminalRecordStatus, TrainingStatus, Interestforfulltime, Repeater,
                    costperhour, chargeperhour, status, passportid, EmploymentAgreement,
                    employeeidno, employeeroleid, employeeenglishrating, employeeExperienceRating,
                    contactmethod
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, employees)
            print("Generated demo employees")

            # Generate Events
            current_date = datetime.now()
            events = [
                ("Summer Wedding Gala", "Hilton Cyprus", current_date + timedelta(days=30), current_date + timedelta(days=30, hours=6), 
                 "Luxury wedding event", 8, 4, 6, 6, 12, 15.00, 25.00, 1),
                ("Corporate Conference", "Four Seasons Hotel", current_date + timedelta(days=45), current_date + timedelta(days=45, hours=8),
                 "Annual business conference", 6, 3, 5, 4, 9, 18.00, 30.00, 2),
                ("Beach Party Event", "Columbia Beach Resort", current_date + timedelta(days=60), current_date + timedelta(days=60, hours=5),
                 "Summer beach celebration", 10, 6, 8, 8, 16, 16.00, 28.00, 3),
                ("New Year's Celebration", "Parklane Resort", current_date + timedelta(days=15), current_date + timedelta(days=15, hours=7),
                 "Grand New Year's party", 12, 8, 10, 10, 20, 20.00, 35.00, 4)
            ]
            cursor.executemany("""
                INSERT INTO event (EventName, EventLocation, EventStart, EventEnd, notes, 
                                 WaitersNeeded, BartendersNeeded, MaleEmployees, FemaleEmployees,
                                 TotalEmployees, EventPerHourcost, EventPerHourselling, Customerid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, events)
            print("Generated demo events")

            # Generate Shifts
            events_query = "SELECT EventID, EventStart, EventEnd FROM event"
            cursor.execute(events_query)
            events = cursor.fetchall()
            
            for event in events:
                shift_types = ['Full', 'Partial']
                for i in range(2):  # Create 2 shifts per event
                    shift_duration = (event['EventEnd'] - event['EventStart']) / 2
                    shift_start = event['EventStart'] + (shift_duration * i)
                    shift_end = shift_start + shift_duration
                    
                    shift = (
                        event['EventID'],
                        f"Shift {i+1} for Event {event['EventID']}",
                        random.choice(shift_types),
                        shift_start,
                        shift_end,
                        Decimal(str(shift_duration.total_seconds() / 3600)).quantize(Decimal('0.00'))  # total_hours
                    )
                    cursor.execute("""
                        INSERT INTO shifts (eventid, shiftname, shifttype, shiftstart, shiftend, total_hours)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, shift)
            print("Generated demo shifts")

            # Assign Employees to Shifts
            cursor.execute("SELECT shiftid FROM shifts")
            shifts = cursor.fetchall()
            cursor.execute("SELECT employeeid FROM employee")
            employees = cursor.fetchall()

            for shift in shifts:
                # Randomly assign 3-6 employees to each shift
                selected_employees = random.sample(employees, random.randint(3, 6))
                for employee in selected_employees:
                    hours = Decimal(str(random.uniform(4.0, 8.0))).quantize(Decimal('0.00'))
                    cursor.execute("""
                        INSERT INTO employee_shifts (shiftid, employeeid, hours)
                        VALUES (%s, %s, %s)
                    """, (shift['shiftid'], employee['employeeid'], hours))
            print("Generated demo shift assignments")

            connection.commit()
            print("\nAll demo data generated successfully!")

    except Exception as e:
        print(f"Error generating demo data: {e}")
        connection.rollback()
    finally:
        # Make sure to re-enable foreign key checks even if there was an error
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.close()

if __name__ == "__main__":
    generate_demo_data() 