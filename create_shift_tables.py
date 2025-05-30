import pymysql

def create_shift_tables():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Create shift table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shift (
                    shiftid INT NOT NULL AUTO_INCREMENT,
                    eventid INT NOT NULL,
                    shiftname VARCHAR(255) NOT NULL,
                    shiftstart DATETIME NOT NULL,
                    shiftend DATETIME NOT NULL,
                    shifttype ENUM('Full', 'Partial') NOT NULL DEFAULT 'Full',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (shiftid),
                    FOREIGN KEY (eventid) REFERENCES event(EventID) ON DELETE CASCADE
                )
            ''')
            
            # Create employee_shift table (for assigning employees to shifts)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_shift (
                    employee_shiftid INT NOT NULL AUTO_INCREMENT,
                    shiftid INT NOT NULL,
                    employeeid INT NOT NULL,
                    hours DECIMAL(5,2) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (employee_shiftid),
                    FOREIGN KEY (shiftid) REFERENCES shift(shiftid) ON DELETE CASCADE,
                    FOREIGN KEY (employeeid) REFERENCES employee(employeeid) ON DELETE CASCADE,
                    UNIQUE KEY unique_employee_shift (shiftid, employeeid)
                )
            ''')
            
            conn.commit()
            print("Shift and employee_shift tables created successfully!")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_shift_tables() 