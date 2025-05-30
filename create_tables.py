import pymysql
from config import app

def create_tables():
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml'
        )

        with connection.cursor() as cursor:
            # Create event table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS `event` (
                    `EventID` int NOT NULL AUTO_INCREMENT,
                    `Customerid` int DEFAULT NULL,
                    `EventName` varchar(255) DEFAULT NULL,
                    `EventLocation` varchar(255) DEFAULT NULL,
                    `EventStart` datetime DEFAULT NULL,
                    `EventEnd` datetime DEFAULT NULL,
                    `notes` text,
                    `WaitersNeeded` int DEFAULT '0',
                    `BartendersNeeded` int DEFAULT '0',
                    `MaleEmployees` int DEFAULT '0',
                    `FemaleEmployees` int DEFAULT '0',
                    `TotalEmployees` int DEFAULT '0',
                    `EventDurationHours` int GENERATED ALWAYS AS (timestampdiff(HOUR,`EventStart`,`EventEnd`)) STORED,
                    `EventTotalHours` int GENERATED ALWAYS AS ((`TotalEmployees` * `EventDurationHours`)) STORED,
                    `EventPerHourcost` decimal(10,2) DEFAULT '0.00',
                    `EventPerHourselling` decimal(10,2) DEFAULT '0.00',
                    `EventStage` enum('Creation','Invoiced','Bank Export','Completed') DEFAULT 'Creation',
                    `totalhours` decimal(10,2) DEFAULT '0.00',
                    `totalcost` decimal(10,2) DEFAULT '0.00',
                    `totalselling` decimal(10,2) DEFAULT '0.00',
                    `totalprofit` decimal(10,2) DEFAULT '0.00',
                    `totalshifthours` decimal(10,2) DEFAULT '0.00',
                    PRIMARY KEY (`EventID`)
                )
            ''')

            # Create customer table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS `customer` (
                    `customerid` int NOT NULL AUTO_INCREMENT,
                    `customer_name` varchar(255) NOT NULL,
                    `contact_person` varchar(255),
                    `email` varchar(255),
                    `phone` varchar(50),
                    `address` text,
                    `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`customerid`)
                )
            ''')

            # Add foreign key constraint
            cursor.execute('''
                ALTER TABLE `event`
                ADD CONSTRAINT `event_ibfk_1` 
                FOREIGN KEY (`Customerid`) 
                REFERENCES `customer` (`customerid`)
            ''')

            # Create employee role table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS `employeerole` (
                    `employeeroleid` int NOT NULL AUTO_INCREMENT,
                    `employeerolename` varchar(255) NOT NULL UNIQUE,
                    `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`employeeroleid`)
                )
            ''')

            # Insert default employee roles
            cursor.execute('''
                INSERT IGNORE INTO employeerole (employeerolename)
                VALUES 
                ('Waiter'),
                ('Bartender'),
                ('Supervisor'),
                ('Manager')
            ''')

            connection.commit()
            print("Tables created successfully!")

            # Insert sample customer data
            cursor.execute('''
                INSERT INTO customer (customer_name, contact_person, email, phone)
                VALUES 
                ('Sample Customer 1', 'John Doe', 'john@example.com', '1234567890'),
                ('Sample Customer 2', 'Jane Smith', 'jane@example.com', '0987654321')
            ''')

            # Insert sample event data
            cursor.execute('''
                INSERT INTO event (
                    Customerid, EventName, EventLocation, EventStart, EventEnd,
                    WaitersNeeded, BartendersNeeded, EventPerHourcost, EventPerHourselling
                )
                VALUES 
                (1, 'Sample Event 1', 'Athens', '2024-03-20 14:00:00', '2024-03-20 20:00:00',
                 2, 1, 15.00, 25.00),
                (2, 'Sample Event 2', 'Thessaloniki', '2024-03-25 16:00:00', '2024-03-25 23:00:00',
                 3, 2, 15.00, 25.00)
            ''')

            connection.commit()
            print("Sample data inserted successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        connection.close()

if __name__ == "__main__":
    create_tables() 