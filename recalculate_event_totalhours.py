import pymysql

def recalculate_all_event_totalhours():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='V0sp0r0si968!',
        database='sml',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            # Get all event IDs
            cursor.execute("SELECT EventID FROM event")
            event_ids = [row['EventID'] for row in cursor.fetchall()]
            for event_id in event_ids:
                cursor.execute("""
                    SELECT COALESCE(SUM(es.hours), 0)
                    FROM shifts s
                    JOIN employee_shifts es ON s.shiftid = es.shiftid
                    WHERE s.eventid = %s
                """, (event_id,))
                totalhours = cursor.fetchone()['COALESCE(SUM(es.hours), 0)']
                cursor.execute(
                    "UPDATE event SET totalhours = %s WHERE EventID = %s",
                    (totalhours, event_id)
                )
                print(f"Event {event_id}: totalhours set to {totalhours}")
            conn.commit()
        print("All event totalhours updated successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    recalculate_all_event_totalhours()