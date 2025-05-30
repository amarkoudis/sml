#!/usr/bin/env python3
"""
This script updates the EventStage to "Completed" for all events 
that have associated invoices with a status of "Sent" or "Paid"
"""

import pymysql
from datetime import datetime

def main():
    print("Updating event statuses based on sent invoices...")
    try:
        # Connect to the database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Find events with sent invoices
            query = """
            SELECT DISTINCT i.event_id 
            FROM invoice i 
            WHERE i.status IN ('Sent', 'Paid') 
            AND i.event_id IS NOT NULL
            """
            cursor.execute(query)
            events_to_update = cursor.fetchall()
            
            if not events_to_update:
                print("No events found with sent invoices.")
                return
            
            event_count = 0
            # Update each event's status
            for event in events_to_update:
                event_id = event['event_id']
                
                # Get current event status
                cursor.execute("SELECT EventStage FROM event WHERE EventID = %s", (event_id,))
                event_data = cursor.fetchone()
                
                if not event_data:
                    print(f"Event ID {event_id} not found!")
                    continue
                
                current_status = event_data['EventStage']
                if current_status == "Completed":
                    continue  # Skip already completed events
                
                # Update to Completed
                update_query = "UPDATE event SET EventStage = %s WHERE EventID = %s"
                cursor.execute(update_query, ("Completed", event_id))
                event_count += 1
                print(f"Updated event ID {event_id} from '{current_status}' to 'Completed'")
            
            conn.commit()
            print(f"Updated {event_count} events to Completed status.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 