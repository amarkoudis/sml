import pymysql
from datetime import datetime

def update_event_table():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='V0sp0r0si968!',
            database='sml',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Backup existing data if needed
            cursor.execute("SELECT * FROM event")
            existing_events = cursor.fetchall()
            
            # Drop and recreate the table
            cursor.execute("""
                DROP TABLE IF EXISTS event;
            """)
            
            cursor.execute("""
                CREATE TABLE `event` (
                    `EventID` int NOT NULL AUTO_INCREMENT,
                    `Customerid` int DEFAULT NULL,
                    `EventName` varchar(255) DEFAULT NULL,
                    `EventLocation` varchar(255) DEFAULT NULL,
                    `EventStart` datetime DEFAULT NULL,
                    `EventEnd` datetime DEFAULT NULL,
                    `notes` text,
                    `WaitersNeeded` int DEFAULT '0',
                    `BartendersNeeded` int DEFAULT '0',
                    `MaleEmployees` int DEFAULT '0',
                    `FemaleEmployees` int DEFAULT '0',
                    `TotalEmployees` int DEFAULT '0',
                    `EventDurationHours` int GENERATED ALWAYS AS (timestampdiff(HOUR,`EventStart`,`EventEnd`)) STORED,
                    `EventTotalHours` int GENERATED ALWAYS AS ((`TotalEmployees` * `EventDurationHours`)) STORED,
                    `EventPerHourcost` decimal(10,2) DEFAULT '0.00',
                    `EventPerHourselling` decimal(10,2) DEFAULT '0.00',
                    `EventStage` enum('Creation','Invoiced','Bank Export','Completed') DEFAULT 'Creation',
                    `totalhours` decimal(10,2) DEFAULT '0.00',
                    `totalcost` decimal(10,2) DEFAULT '0.00',
                    `totalselling` decimal(10,2) DEFAULT '0.00',
                    `totalprofit` decimal(10,2) DEFAULT '0.00',
                    `totalshifthours` decimal(10,2) DEFAULT '0.00',
                    PRIMARY KEY (`EventID`),
                    KEY `Customerid` (`Customerid`),
                    CONSTRAINT `event_ibfk_1` FOREIGN KEY (`Customerid`) REFERENCES `customer` (`customerid`)
                )
            """)
            
            # Reinsert existing data if there was any
            if existing_events:
                for event in existing_events:
                    cursor.execute("""
                        INSERT INTO event (
                            EventID, Customerid, EventName, EventLocation, 
                            EventStart, EventEnd, notes, WaitersNeeded, 
                            BartendersNeeded, MaleEmployees, FemaleEmployees, 
                            TotalEmployees, EventPerHourcost, EventPerHourselling, 
                            EventStage, totalhours, totalcost, totalselling, 
                            totalprofit, totalshifthours
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        event.get('EventID'),
                        event.get('Customerid'),
                        event.get('EventName'),
                        event.get('EventLocation'),
                        event.get('EventStart'),
                        event.get('EventEnd'),
                        event.get('notes'),
                        event.get('WaitersNeeded', 0),
                        event.get('BartendersNeeded', 0),
                        event.get('MaleEmployees', 0),
                        event.get('FemaleEmployees', 0),
                        event.get('TotalEmployees', 0),
                        event.get('EventPerHourcost', 0.00),
                        event.get('EventPerHourselling', 0.00),
                        event.get('EventStage', 'Creation'),
                        event.get('totalhours', 0.00),
                        event.get('totalcost', 0.00),
                        event.get('totalselling', 0.00),
                        event.get('totalprofit', 0.00),
                        event.get('totalshifthours', 0.00)
                    ))
            
            # Add a sample event if table is empty
            cursor.execute("SELECT COUNT(*) as count FROM event")
            if cursor.fetchone()['count'] == 0:
                cursor.execute("""
                    INSERT INTO event (
                        Customerid, EventName, EventLocation, EventStart, 
                        EventEnd, notes, WaitersNeeded, BartendersNeeded
                    ) VALUES (
                        (SELECT customerid FROM customer LIMIT 1),
                        'Sample Event',
                        'Sample Location',
                        NOW(),
                        DATE_ADD(NOW(), INTERVAL 4 HOUR),
                        'Sample event notes',
                        2,
                        1
                    )
                """)
            
            conn.commit()
            print("Event table updated successfully!")
            
    except Exception as e:
        print(f"Error updating event table: {str(e)}")
        conn.rollback()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_event_table() 