"""
Data fix script to ensure only one company record exists in the system.
This script checks if multiple company records exist and keeps only the first one.
It assigns all employees to this company and then deletes other company records.
"""

import pymysql
import sys
import os

# Add parent directory to path so that imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def connect_to_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        cursorclass=pymysql.cursors.DictCursor
    )

def fix_company_data():
    conn = None
    try:
        conn = connect_to_db()
        with conn.cursor() as cursor:
            # Get all companies ordered by ID (keep the oldest company)
            cursor.execute('SELECT companyid FROM company ORDER BY companyid')
            companies = cursor.fetchall()
            
            if not companies:
                print("No company records found. Nothing to fix.")
                return
                
            if len(companies) == 1:
                print("Only one company record exists. No fix needed.")
                return
                
            # Keep the first company
            company_to_keep = companies[0]['companyid']
            companies_to_delete = [c['companyid'] for c in companies[1:]]
            
            print(f"Found {len(companies)} company records. Keeping company ID {company_to_keep}, deleting {len(companies_to_delete)} other records.")
            
            # Reassign all employees to the company we're keeping
            employee_update_count = 0
            for company_id in companies_to_delete:
                cursor.execute('''
                    UPDATE employee 
                    SET companyid = %s 
                    WHERE companyid = %s
                ''', (company_to_keep, company_id))
                employee_update_count += cursor.rowcount
            
            print(f"Reassigned {employee_update_count} employees to company ID {company_to_keep}")
            
            # Now delete the extra company records
            delete_count = 0
            for company_id in companies_to_delete:
                try:
                    cursor.execute('DELETE FROM company WHERE companyid = %s', (company_id,))
                    delete_count += cursor.rowcount
                except Exception as e:
                    print(f"Error deleting company ID {company_id}: {str(e)}")
            
            conn.commit()
            print(f"Successfully deleted {delete_count} company records.")
            print("Data fix completed successfully.")
            
    except Exception as e:
        print(f"Error fixing company data: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting company data fix...")
    fix_company_data()
    print("Finished.") 