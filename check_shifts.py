import pymysql
from datetime import datetime

def check_shifts():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with conn.cursor() as cursor:
            # Check shifts
            print("\n=== Shifts for Event ID 1 ===")
            cursor.execute('''
                SELECT 
                    s.shiftid,
                    s.shiftname,
                    s.shifttype,
                    s.shiftstart,
                    s.shiftend,
                    COUNT(DISTINCT es.employeeid) as assigned_employees
                FROM shifts s
                LEFT JOIN employee_shifts es ON s.shiftid = es.shiftid
                WHERE s.eventid = 1
                GROUP BY s.shiftid
            ''')
            shifts = cursor.fetchall()
            for shift in shifts:
                print(f"\nShift ID: {shift['shiftid']}")
                print(f"Name: {shift['shiftname']}")
                print(f"Type: {shift['shifttype']}")
                print(f"Start: {shift['shiftstart']}")
                print(f"End: {shift['shiftend']}")
                print(f"Assigned Employees: {shift['assigned_employees']}")
            
            # Check employee assignments
            print("\n=== Employee Assignments for Event ID 1 ===")
            cursor.execute('''
                SELECT 
                    e.employeeid,
                    e.employeename,
                    s.shiftid,
                    s.shiftname,
                    es.hours
                FROM employee e
                JOIN employee_shifts es ON e.employeeid = es.employeeid
                JOIN shifts s ON es.shiftid = s.shiftid
                WHERE s.eventid = 1
                ORDER BY e.employeename, s.shiftstart
            ''')
            assignments = cursor.fetchall()
            for assignment in assignments:
                print(f"\nEmployee: {assignment['employeename']} (ID: {assignment['employeeid']})")
                print(f"Shift: {assignment['shiftname']} (ID: {assignment['shiftid']})")
                print(f"Hours: {assignment['hours']}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_shifts() 