-- Create system_settings table to store global configuration values
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    setting_name VARCHAR(255) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_description TEXT,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default settings for employer and employee contributions
INSERT INTO system_settings (setting_name, setting_value, setting_description) VALUES
('employer_contribution_percentage', '13.0', 'Percentage of employee cost that the employer contributes'),
('employee_contribution_percentage', '8.0', 'Percentage of employee cost that is deducted from employee'),
('vat_rate_default', '19.0', 'Default VAT rate for invoices and calculations'),
('system_currency', 'EUR', 'Default currency symbol for the system'); 