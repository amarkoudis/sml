import pymysql

def create_banks_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml'
        )
        
        with conn.cursor() as cursor:
            # Create banks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banks (
                    bankid INT NOT NULL AUTO_INCREMENT,
                    bankname VARCHAR(255) NOT NULL,
                    biccode VARCHAR(11) DEFAULT NULL,
                    PRIMARY KEY (bankid)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            ''')
            
            # Add foreign key to customer table
            try:
                cursor.execute('''
                    ALTER TABLE customer
                    ADD CONSTRAINT fk_customer_bank
                    FOREIGN KEY (bankid)
                    REFERENCES banks(bankid)
                    ON DELETE SET NULL
                ''')
                print("Added foreign key to customer table")
            except Exception as e:
                print(f"Foreign key might already exist: {str(e)}")

            conn.commit()
            print("Banks table created successfully")

    except Exception as e:
        print(f"Error creating table: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_banks_table() 