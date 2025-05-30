import pymysql

def create_employee_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Create employee table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee (
                    employeeid INT NOT NULL AUTO_INCREMENT,
                    transactiontype ENUM('S','B') NOT NULL DEFAULT 'S',
                    employeename VARCHAR(255) NOT NULL,
                    companyid INT NOT NULL,
                    bankid INT NOT NULL,
                    swiftno VARCHAR(11) NOT NULL,
                    currency CHAR(4) DEFAULT NULL,
                    address TEXT NOT NULL,
                    address2 TEXT,
                    zipcode VARCHAR(10) DEFAULT NULL,
                    city ENUM('Nicosia','Limassol','Larnaca','Famagusta','Paphos') NOT NULL,
                    age INT NOT NULL,
                    gender ENUM('Male','Female') NOT NULL,
                    tel VARCHAR(15) DEFAULT NULL,
                    nationality ENUM('Cypriot','EU','Foreigner') NOT NULL DEFAULT 'Cypriot',
                    email VARCHAR(255) NOT NULL,
                    currentworkplace ENUM('Yes','No') DEFAULT 'No',
                    SocialInsuranceno VARCHAR(50) DEFAULT NULL,
                    Tattoo ENUM('Yes','No') DEFAULT 'No',
                    AgreementStatus ENUM('Yes','No') DEFAULT 'No',
                    CriminalRecordStatus ENUM('Yes','No') DEFAULT 'No',
                    TrainingStatus ENUM('Yes','No') DEFAULT 'No',
                    Interestforfulltime ENUM('Yes','No') DEFAULT 'No',
                    Repeater ENUM('Yes','No') DEFAULT 'No',
                    costperhour DECIMAL(10,2) DEFAULT NULL,
                    chargeperhour DECIMAL(10,2) NOT NULL,
                    status ENUM('Active','Inactive') DEFAULT 'Active',
                    passportid VARCHAR(50) NOT NULL,
                    EmploymentAgreement VARCHAR(255) NOT NULL,
                    employeeidno INT NOT NULL,
                    employeeroleid INT NOT NULL DEFAULT '1',
                    employeeenglishrating ENUM('1','2','3','4','5') NOT NULL DEFAULT '1',
                    employeeExperienceRating ENUM('1','2','3','4','5') NOT NULL DEFAULT '1',
                    contactmethod ENUM('email','sms') NOT NULL DEFAULT 'email',
                    PRIMARY KEY (employeeid),
                    KEY companyid (companyid),
                    KEY bankid (bankid),
                    CONSTRAINT employee_ibfk_1 FOREIGN KEY (companyid) REFERENCES company (companyid),
                    CONSTRAINT employee_ibfk_2 FOREIGN KEY (bankid) REFERENCES banks (bankid)
                )
            ''')
            
            conn.commit()
            print("Employee table created successfully!")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_employee_table() 