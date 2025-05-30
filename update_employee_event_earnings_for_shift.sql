DROP PROCEDURE IF EXISTS update_employee_event_earnings_for_shift;
DELIMITER $$

CREATE PROCEDURE update_employee_event_earnings_for_shift(IN p_employeeid INT, IN p_eventid INT)
BEGIN
    DECLARE v_total_hours DECIMAL(10,2);
    DECLARE v_costperhour DECIMAL(10,2);
    DECLARE v_sellingperhour DECIMAL(10,2);
    DECLARE v_gross_earnings DECIMAL(10,2);
    DECLARE v_social_employee DECIMAL(10,2);
    DECLARE v_gesy_employee DECIMAL(10,2);
    DECLARE v_social_employer DECIMAL(10,2);
    DECLARE v_gesy_employer DECIMAL(10,2);
    DECLARE v_cohesion_employer DECIMAL(10,2);
    DECLARE v_redundancy_employer DECIMAL(10,2);
    DECLARE v_industrial_employer DECIMAL(10,2);

    -- Get contribution rates from contribution_settings (or use defaults)
    SELECT 
        COALESCE((SELECT CAST(setting_value AS DECIMAL(10,2)) FROM contribution_settings WHERE setting_name = 'social_employee'), 8.8),
        COALESCE((SELECT CAST(setting_value AS DECIMAL(10,2)) FROM contribution_settings WHERE setting_name = 'gesy_employee'), 2.65),
        COALESCE((SELECT CAST(setting_value AS DECIMAL(10,2)) FROM contribution_settings WHERE setting_name = 'social_employer'), 8.8),
        COALESCE((SELECT CAST(setting_value AS DECIMAL(10,2)) FROM contribution_settings WHERE setting_name = 'gesy_employer'), 2.9),
        COALESCE((SELECT CAST(setting_value AS DECIMAL(10,2)) FROM contribution_settings WHERE setting_name = 'cohesion_employer'), 2.0),
        COALESCE((SELECT CAST(setting_value AS DECIMAL(10,2)) FROM contribution_settings WHERE setting_name = 'redundancy_employer'), 1.2),
        COALESCE((SELECT CAST(setting_value AS DECIMAL(10,2)) FROM contribution_settings WHERE setting_name = 'industrial_employer'), 0.05)
    INTO
        v_social_employee, v_gesy_employee, v_social_employer,
        v_gesy_employer, v_cohesion_employer, v_redundancy_employer, v_industrial_employer; 

    -- Get the total hours and rates (using event rates instead of employee rates)
    SELECT
        COALESCE(SUM(es.hours), 0),
        evt.EventPerHourcost,
        evt.EventPerHourselling
    INTO
        v_total_hours, v_costperhour, v_sellingperhour
    FROM
        employee_shifts es
    JOIN
        shifts s ON es.shiftid = s.shiftid
    JOIN
        employee e ON es.employeeid = e.employeeid
    JOIN
        event evt ON s.eventid = evt.EventID
    WHERE
        es.employeeid = p_employeeid
        AND s.eventid = p_eventid
    GROUP BY
        evt.EventPerHourcost, evt.EventPerHourselling;

    -- Calculate gross earnings
    SET v_gross_earnings = v_total_hours * v_costperhour;

    -- If hours are 0, delete the record
    IF v_total_hours = 0 THEN
        DELETE FROM employee_event_earnings
        WHERE employeeid = p_employeeid AND eventid = p_eventid;
    ELSE
        -- Calculate contributions and earnings
        REPLACE INTO employee_event_earnings (
            employeeid, eventid, total_hours, costperhour, sellingperhour,
            gross_earnings, social_employee, gesy_employee, total_employee_contrib,
            social_employer, gesy_employer, cohesion_employer, redundancy_employer,
            industrial_employer, total_employer_contrib, net_earnings, total_cost
        ) VALUES (
            p_employeeid, p_eventid, v_total_hours, v_costperhour, v_sellingperhour,

            v_gross_earnings,
            (v_gross_earnings * v_social_employee / 100),
            (v_gross_earnings * v_gesy_employee / 100),
            (v_gross_earnings * (v_social_employee + v_gesy_employee) / 100),
            (v_gross_earnings * v_social_employer / 100),
            (v_gross_earnings * v_gesy_employer / 100),
            (v_gross_earnings * v_cohesion_employer / 100),
            (v_gross_earnings * v_redundancy_employer / 100),
            (v_gross_earnings * v_industrial_employer / 100),
            (v_gross_earnings * (v_social_employer + v_gesy_employer + v_cohesion_employer + v_redundancy_employer + v_industrial_employer) / 100),
            (v_gross_earnings - (v_gross_earnings * (v_social_employee + v_gesy_employee) / 100)),
            (v_gross_earnings + (v_gross_earnings * (v_social_employer + v_gesy_employer + v_cohesion_employer + v_redundancy_employer + v_industrial_employer) / 100))
        );
    END IF;
END$$

DELIMITER ; 