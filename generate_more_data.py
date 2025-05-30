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

def generate_more_data():
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            # Temporarily disable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # Clear existing data in reverse order of dependencies, except company
            tables = [
                'employee_shifts',
                'shifts',
                'event',
                'employee',
                'customer',
                'banks'
            ]
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            # Generate Banks (More Cyprus banks)
            banks = [
                ("Bank of Cyprus", "BCYPCY2N"),
                ("Hellenic Bank", "HEBACY2N"),
                ("Alpha Bank Cyprus", "ABKLCY2N"),
                ("Eurobank Cyprus", "ERBKCY2N"),
                ("RCB Bank", "RCBLCY2I"),
                ("Astrobank", "PIRBCY2N"),
                ("Cyprus Development Bank", "CYBKCY2N"),
                ("Societe Generale Cyprus", "SOGECY2N")
            ]
            cursor.executemany(
                "INSERT INTO banks (bankname, biccode) VALUES (%s, %s)",
                banks
            )
            print("Generated more demo banks")

            # Generate Customers (More hotels and venues)
            customers = [
                ("Hilton Cyprus", "22 Arch. Makarios III Avenue", "+35722377777", "events@hilton.com.cy", "Maria Georgiou", 1),
                ("Four Seasons Hotel", "67-69 Amathus Avenue", "+35725858000", "events@fourseasons.com.cy", "Andreas Dimitriou", 2),
                ("Columbia Beach Resort", "Pissouri Bay", "+35725833000", "events@columbia-hotels.com", "Elena Papadopoulou", 3),
                ("Parklane Resort", "11 Giannou Kranidioti Street", "+35725862000", "events@parklane.com.cy", "Christos Andreou", 1),
                ("Amara Hotel", "95 Amathus Avenue", "+35725834000", "events@amarahotel.com", "Sophia Kyriacou", 5),
                ("Elysium Hotel", "Queen Verenikis Street", "+35726844444", "events@elysium.com.cy", "Nicolas Antoniou", 6),
                ("Annabelle Hotel", "10 Poseidonos Avenue", "+35726885111", "events@annabelle.com.cy", "Anna Christou", 7),
                ("The Royal Apollonia", "Apollonia Beach", "+35725834000", "events@royalapollonia.com", "Panayiotis Michael", 8),
                ("Mediterranean Beach Hotel", "71 Amathus Avenue", "+35725311777", "events@medbeach.com", "Georgia Nicolaou", 1),
                ("St Raphael Resort", "502 Amathus Avenue", "+35725834000", "events@straphael.com", "Marios Andreou", 2)
            ]
            cursor.executemany(
                "INSERT INTO customer (customername, customeraddress, customerphone, customeremail, contactpersonname, bankid) VALUES (%s, %s, %s, %s, %s, %s)",
                customers
            )
            print("Generated more demo customers")

            # Generate Employees (50 employees)
            cities = ['Nicosia', 'Limassol', 'Larnaca', 'Paphos', 'Famagusta']
            genders = ['Male', 'Female']
            nationalities = ['Cypriot', 'EU', 'Foreigner']
            yes_no = ['Yes', 'No']
            ratings = ['1', '2', '3', '4', '5']
            contact_methods = ['email', 'sms']
            
            cypriot_first_names_male = ['Andreas', 'George', 'Costas', 'Michalis', 'Christos', 'Nicos', 'Panayiotis', 'Stavros']
            cypriot_first_names_female = ['Maria', 'Elena', 'Christina', 'Sophia', 'Anna', 'Georgia', 'Eleni', 'Andri']
            cypriot_last_names = ['Georgiou', 'Christou', 'Andreou', 'Kyriacou', 'Nicolaou', 'Demetriou', 'Constantinou', 'Papageorgiou']

            employees = []
            for i in range(50):
                gender = random.choice(genders)
                nationality = random.choice(nationalities)
                
                if nationality == 'Cypriot':
                    first_name = random.choice(cypriot_first_names_male if gender == 'Male' else cypriot_first_names_female)
                    last_name = random.choice(cypriot_last_names)
                else:
                    first_name = "John" if gender == "Male" else "Jane"
                    last_name = f"International{i+1}"
                
                employee = (
                    'S',  # transactiontype
                    f"{first_name} {last_name}",  # employeename
                    random.randint(1, 3),  # companyid
                    random.randint(1, 8),  # bankid
                    f"SW{str(i+1).zfill(8)}",  # swiftno
                    "EUR",  # currency
                    f"{random.randint(1, 100)} {random.choice(['Makarios', 'Griva Digeni', 'Anexartisias', 'Ledras'])} Street",  # address
                    f"Flat {random.randint(1, 50)}",  # address2
                    f"{random.randint(1000, 9999)}",  # zipcode
                    random.choice(cities),  # city
                    random.randint(20, 45),  # age
                    gender,  # gender
                    f"+357{random.randint(95000000, 99999999)}",  # tel
                    nationality,  # nationality
                    f"{first_name.lower()}.{last_name.lower()}@email.com",  # email
                    random.choice(yes_no),  # currentworkplace
                    f"SI{str(random.randint(1000, 9999))}",  # SocialInsuranceno
                    random.choice(yes_no),  # Tattoo
                    'Yes',  # AgreementStatus
                    'No',  # CriminalRecordStatus
                    random.choice(['Yes', 'Yes', 'No']),  # TrainingStatus (bias towards trained)
                    random.choice(yes_no),  # Interestforfulltime
                    random.choice(yes_no),  # Repeater
                    Decimal(str(random.uniform(8.0, 15.0))).quantize(Decimal('0.00')),  # costperhour
                    Decimal(str(random.uniform(15.0, 25.0))).quantize(Decimal('0.00')),  # chargeperhour
                    'Active',  # status
                    f"P{str(random.randint(100000, 999999))}",  # passportid
                    f"EA{str(random.randint(1000, 9999))}",  # EmploymentAgreement
                    i + 2000,  # employeeidno
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
            print("Generated more demo employees")

            # Generate Events (More events with varied types)
            current_date = datetime.now()
            events = []
            event_types = [
                ("Wedding Reception", 8, 4, 6, 6, 12, 15.00, 25.00),
                ("Corporate Conference", 6, 3, 5, 4, 9, 18.00, 30.00),
                ("Beach Party", 10, 6, 8, 8, 16, 16.00, 28.00),
                ("Gala Dinner", 12, 8, 10, 10, 20, 20.00, 35.00),
                ("Product Launch", 8, 4, 6, 6, 12, 17.00, 28.00),
                ("Fashion Show", 10, 5, 8, 8, 16, 19.00, 32.00),
                ("Charity Ball", 15, 8, 12, 12, 24, 22.00, 38.00),
                ("Wine Tasting", 6, 4, 5, 5, 10, 16.00, 27.00)
            ]

            for i in range(20):  # Generate 20 events
                event_type = random.choice(event_types)
                event_date = current_date + timedelta(days=random.randint(15, 180))
                event_duration = random.randint(4, 8)  # hours
                customer_id = random.randint(1, 10)
                
                event = (
                    f"{event_type[0]} #{i+1}",  # EventName
                    random.choice([c[0] for c in customers]),  # EventLocation
                    event_date,  # EventStart
                    event_date + timedelta(hours=event_duration),  # EventEnd
                    f"Cyprus {event_type[0]} event",  # notes
                    event_type[1],  # WaitersNeeded
                    event_type[2],  # BartendersNeeded
                    event_type[3],  # MaleEmployees
                    event_type[4],  # FemaleEmployees
                    event_type[5],  # TotalEmployees
                    event_type[6],  # EventPerHourcost
                    event_type[7],  # EventPerHourselling
                    customer_id  # Customerid
                )
                events.append(event)

            cursor.executemany("""
                INSERT INTO event (EventName, EventLocation, EventStart, EventEnd, notes, 
                                 WaitersNeeded, BartendersNeeded, MaleEmployees, FemaleEmployees,
                                 TotalEmployees, EventPerHourcost, EventPerHourselling, Customerid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, events)
            print("Generated more demo events")

            # Generate Shifts for each event
            events_query = "SELECT EventID, EventStart, EventEnd FROM event"
            cursor.execute(events_query)
            events = cursor.fetchall()
            
            for event in events:
                shift_types = ['Full', 'Partial']
                num_shifts = random.randint(2, 3)  # 2-3 shifts per event
                shift_duration = (event['EventEnd'] - event['EventStart']) / num_shifts
                
                for i in range(num_shifts):
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
            print("Generated more demo shifts")

            # Assign Employees to Shifts
            cursor.execute("SELECT shiftid FROM shifts")
            shifts = cursor.fetchall()
            cursor.execute("SELECT employeeid FROM employee")
            employees = cursor.fetchall()

            for shift in shifts:
                # Assign 4-8 employees to each shift
                selected_employees = random.sample(employees, random.randint(4, 8))
                for employee in selected_employees:
                    hours = Decimal(str(random.uniform(4.0, 8.0))).quantize(Decimal('0.00'))
                    cursor.execute("""
                        INSERT INTO employee_shifts (shiftid, employeeid, hours)
                        VALUES (%s, %s, %s)
                    """, (shift['shiftid'], employee['employeeid'], hours))
            print("Generated more demo shift assignments")

            connection.commit()
            print("\nAll additional demo data generated successfully!")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    generate_more_data() 