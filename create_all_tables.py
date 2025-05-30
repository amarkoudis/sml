import pymysql

def create_all_tables():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # Create banks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS banks (
                    bankid INT AUTO_INCREMENT PRIMARY KEY,
                    bankname VARCHAR(100) NOT NULL,
                    biccode VARCHAR(50)
                )
            """)
            
            # Create company table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company (
                    companyid INT NOT NULL AUTO_INCREMENT,
                    companyname VARCHAR(255) NOT NULL,
                    companydebitaccount VARCHAR(50) DEFAULT NULL,
                    bankid INT NOT NULL,
                    transactiontype ENUM('S','B') NOT NULL DEFAULT 'S',
                    PRIMARY KEY (companyid),
                    FOREIGN KEY (bankid) REFERENCES banks(bankid)
                )
            """)
            
            # Create customer table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer (
                    customerid INT AUTO_INCREMENT PRIMARY KEY,
                    customername VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    phone VARCHAR(20),
                    address VARCHAR(255),
                    bankid INT,
                    FOREIGN KEY (bankid) REFERENCES banks(bankid)
                )
            """)
            
            # Create employeerole table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employeerole (
                    roleid INT AUTO_INCREMENT PRIMARY KEY,
                    rolename VARCHAR(50) NOT NULL,
                    description TEXT
                )
            """)
            
            # Create employee table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employee (
                    employeeid INT AUTO_INCREMENT PRIMARY KEY,
                    employeename VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    phone VARCHAR(20),
                    roleid INT,
                    isactive BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (roleid) REFERENCES employeerole(roleid)
                )
            """)
            
            # Create event table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event (
                    EventID INT AUTO_INCREMENT PRIMARY KEY,
                    Customerid INT,
                    EventName VARCHAR(255),
                    EventLocation VARCHAR(255),
                    EventStart DATETIME,
                    EventEnd DATETIME,
                    notes TEXT,
                    WaitersNeeded INT DEFAULT 0,
                    BartendersNeeded INT DEFAULT 0,
                    MaleEmployees INT DEFAULT 0,
                    FemaleEmployees INT DEFAULT 0,
                    TotalEmployees INT DEFAULT 0,
                    EventPerHourcost DECIMAL(10,2) DEFAULT 0.00,
                    EventPerHourselling DECIMAL(10,2) DEFAULT 0.00,
                    EventStage ENUM('Creation','Invoiced','Bank Export','Completed') DEFAULT 'Creation',
                    totalhours DECIMAL(10,2) DEFAULT 0.00,
                    totalcost DECIMAL(10,2) DEFAULT 0.00,
                    totalselling DECIMAL(10,2) DEFAULT 0.00,
                    totalprofit DECIMAL(10,2) DEFAULT 0.00,
                    totalshifthours DECIMAL(10,2) DEFAULT 0.00,
                    FOREIGN KEY (Customerid) REFERENCES customer(customerid)
                )
            """)
            
            # Create shifts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shifts (
                    shiftid INT AUTO_INCREMENT PRIMARY KEY,
                    eventid INT NOT NULL,
                    shiftname VARCHAR(100) NOT NULL,
                    shiftstart DATETIME NOT NULL,
                    shiftend DATETIME NOT NULL,
                    shifttype ENUM('Full', 'Partial') NOT NULL DEFAULT 'Full',
                    FOREIGN KEY (eventid) REFERENCES event(EventID) ON DELETE CASCADE
                )
            """)
            
            # Create employee_shifts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employee_shifts (
                    shiftid INT NOT NULL,
                    employeeid INT NOT NULL,
                    hours DECIMAL(5,2),
                    PRIMARY KEY (shiftid, employeeid),
                    FOREIGN KEY (shiftid) REFERENCES shifts(shiftid) ON DELETE CASCADE,
                    FOREIGN KEY (employeeid) REFERENCES employee(employeeid) ON DELETE CASCADE
                )
            """)
            
            connection.commit()
            print("All tables created successfully!")
            
    except Exception as e:
        print(f"Error creating tables: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    create_all_tables() 