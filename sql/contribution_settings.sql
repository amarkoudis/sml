-- Create contribution settings if they don't exist
INSERT IGNORE INTO contribution_settings (setting_name, setting_value, setting_description)
VALUES 
-- Social Insurance
('social_employee', '8.80', 'Employee social insurance contribution percentage'),
('social_employer', '8.80', 'Employer social insurance contribution percentage'),

-- GESY (Health Insurance)
('gesy_employee', '2.65', 'Employee health insurance (GESY) contribution percentage'),
('gesy_employer', '2.90', 'Employer health insurance (GESY) contribution percentage'),

-- Social Cohesion Fund (employer only)
('cohesion_employee', '0', 'Employee social cohesion fund contribution percentage (typically 0)'),
('cohesion_employer', '2.0', 'Employer social cohesion fund contribution percentage'),

-- Redundancy Fund (employer only)
('redundancy_employee', '0', 'Employee redundancy fund contribution percentage (typically 0)'),
('redundancy_employer', '1.2', 'Employer redundancy fund contribution percentage'),

-- Industrial Fund (employer only)
('industrial_employee', '0', 'Employee industrial fund contribution percentage (typically 0)'),
('industrial_employer', '0.05', 'Employer industrial fund contribution percentage');

-- Update existing main contribution settings to match the totals
UPDATE contribution_settings
SET setting_value = '11.45'
WHERE setting_name = 'employee_contribution_percentage';

UPDATE contribution_settings
SET setting_value = '14.95'
WHERE setting_name = 'employer_contribution_percentage'; 