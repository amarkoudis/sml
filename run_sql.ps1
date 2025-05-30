$sql = Get-Content -Path "sql\add_company_fields.sql" -Raw
mysql -u root -p"V0sp0r0si968!" -D sml -e "$sql" 