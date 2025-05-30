-- Shift Management Tables for MySQL
CREATE TABLE IF NOT EXISTS shifts (
    shiftid INT AUTO_INCREMENT PRIMARY KEY,
    eventid INT NOT NULL,
    shiftname VARCHAR(100) NOT NULL,
    shifttype ENUM('Full', 'Partial') NOT NULL,
    shiftstart DATETIME NOT NULL,
    shiftend DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT valid_shift_times CHECK (shiftend > shiftstart)
);

CREATE TABLE IF NOT EXISTS employee_shifts (
    employee_shift_id INT AUTO_INCREMENT PRIMARY KEY,
    shiftid INT NOT NULL,
    employeeid INT NOT NULL,
    hours DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT unique_employee_shift UNIQUE (shiftid, employeeid),
    CONSTRAINT valid_hours CHECK (hours > 0)
);

-- Create indexes for better performance
CREATE INDEX idx_shifts_eventid ON shifts(eventid);
CREATE INDEX idx_employee_shifts_shiftid ON employee_shifts(shiftid);
CREATE INDEX idx_employee_shifts_employeeid ON employee_shifts(employeeid);

-- Create view for shift details with employee count
CREATE OR REPLACE VIEW shift_details AS
SELECT 
    s.shiftid,
    s.eventid,
    s.shiftname,
    s.shifttype,
    s.shiftstart,
    s.shiftend,
    COUNT(es.employeeid) as employee_count,
    COALESCE(SUM(es.hours), 0) as total_hours
FROM shifts s
LEFT JOIN employee_shifts es ON s.shiftid = es.shiftid
GROUP BY s.shiftid, s.eventid, s.shiftname, s.shifttype, s.shiftstart, s.shiftend; 