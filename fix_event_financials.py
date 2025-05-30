import pymysql

# Database connection settings
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'V0sp0r0si968!',
    'database': 'sml',
    'cursorclass': pymysql.cursors.DictCursor
}

def fix_event_financials():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            # Update all events with the correct calculations
            sql = '''
                UPDATE event
                SET
                    totalcost = totalhours * EventPerHourcost,
                    totalselling = totalhours * EventPerHourselling,
                    totalprofit = (totalhours * EventPerHourselling) - (totalhours * EventPerHourcost)
            '''
            cursor.execute(sql)
            conn.commit()
            print('All event financials recalculated and updated.')
    finally:
        conn.close()

if __name__ == '__main__':
    fix_event_financials() 