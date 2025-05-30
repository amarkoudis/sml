-- Add new fields to the company table
ALTER TABLE company
ADD COLUMN companyaddress VARCHAR(255) DEFAULT NULL,
ADD COLUMN companyphone VARCHAR(20) DEFAULT NULL,
ADD COLUMN companyemail VARCHAR(100) DEFAULT NULL,
ADD COLUMN companyweb VARCHAR(100) DEFAULT NULL,
ADD COLUMN vatno VARCHAR(30) DEFAULT NULL,
ADD COLUMN paymentpolicy VARCHAR(255) DEFAULT NULL,
ADD COLUMN beneficiary VARCHAR(255) DEFAULT NULL,
ADD COLUMN companyiban VARCHAR(50) DEFAULT NULL;

-- Update existing records with placeholder values if needed
-- UPDATE company SET
--     companyaddress = 'Default Address',
--     companyphone = 'Default Phone',
--     companyemail = 'default@example.com',
--     companyweb = 'www.example.com',
--     vatno = 'Default VAT',
--     paymentpolicy = 'Default Payment Policy',
--     beneficiary = 'Default Beneficiary',
--     companyiban = 'Default IBAN'
-- WHERE companyid > 0; 