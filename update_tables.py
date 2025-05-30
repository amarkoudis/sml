import pymysql

def update_database_structure():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml'
        )
        
        with conn.cursor() as cursor:
            # 1. Create banks table
            print("Creating banks table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banks (
                    bankid INT NOT NULL AUTO_INCREMENT,
                    bankname VARCHAR(255) NOT NULL,
                    biccode VARCHAR(11) DEFAULT NULL,
                    PRIMARY KEY (bankid)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            ''')
            print("Banks table created successfully")

            # 2. Add bankid column to customer table if it doesn't exist
            print("Checking customer table structure...")
            cursor.execute("SHOW COLUMNS FROM customer LIKE 'bankid'")
            if not cursor.fetchone():
                print("Adding bankid column to customer table...")
                cursor.execute('''
                    ALTER TABLE customer
                    ADD COLUMN bankid INT DEFAULT NULL
                ''')
                print("Added bankid column to customer table")

            # 3. Add foreign key constraint
            print("Adding foreign key constraint...")
            try:
                cursor.execute('''
                    ALTER TABLE customer
                    ADD CONSTRAINT fk_customer_bank
                    FOREIGN KEY (bankid)
                    REFERENCES banks(bankid)
                    ON DELETE SET NULL
                ''')
                print("Added foreign key constraint successfully")
            except Exception as e:
                print(f"Foreign key constraint error (might already exist): {str(e)}")

            # 4. Check if banks table is empty
            cursor.execute("SELECT COUNT(*) FROM banks")
            count = cursor.fetchone()[0]  # Fixed: Access first element of tuple

            if count == 0:
                print("Adding sample banks...")
                sample_banks = [
                    ("Alpha Bank", "ALPHABANK1"),
                    ("Beta Bank", "BETABANK12"),
                    ("Gamma Bank", "GAMMABANK3")
                ]
                cursor.executemany(
                    "INSERT INTO banks (bankname, biccode) VALUES (%s, %s)",
                    sample_banks
                )
                print("Added sample banks")

            conn.commit()
            print("Database update completed successfully")

    except Exception as e:
        print(f"Error updating database: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_database_structure() 