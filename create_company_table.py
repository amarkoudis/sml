import pymysql

def create_company_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml'
        )
        
        with conn.cursor() as cursor:
            # Drop the table if it exists to avoid any conflicts
            cursor.execute('''
                DROP TABLE IF EXISTS company
            ''')
            print("Dropped existing company table if any")

            # Create company table
            cursor.execute('''
                CREATE TABLE company (
                    companyid INT NOT NULL AUTO_INCREMENT,
                    companyname VARCHAR(255) NOT NULL,
                    companydebitaccount VARCHAR(50) DEFAULT NULL,
                    bankid INT NOT NULL,
                    transactiontype ENUM('S','B') NOT NULL DEFAULT 'S',
                    PRIMARY KEY (companyid),
                    KEY bankid (bankid),
                    CONSTRAINT company_ibfk_1 FOREIGN KEY (bankid) 
                    REFERENCES banks (bankid)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            ''')
            
            # Insert some sample data
            sample_companies = [
                ('Test Company 1', '123456789', 1, 'S'),
                ('Test Company 2', '987654321', 1, 'B'),
                ('Test Company 3', '456789123', 2, 'S')
            ]
            
            cursor.executemany('''
                INSERT INTO company (companyname, companydebitaccount, bankid, transactiontype)
                VALUES (%s, %s, %s, %s)
            ''', sample_companies)
            
            conn.commit()
            print("Company table created and sample data inserted successfully")

    except Exception as e:
        print(f"Error creating table: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_company_table() 