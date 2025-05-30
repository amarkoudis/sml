-- Add company logo field to the company table
ALTER TABLE company
ADD COLUMN company_logo VARCHAR(255) DEFAULT NULL; 