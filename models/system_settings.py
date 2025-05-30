import pymysql

class ContributionSettings:
    """Model for contribution configuration settings"""
    
    @staticmethod
    def get_setting(setting_name, default_value=None):
        """Get a setting value by name"""
        conn = None
        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                sql = "SELECT setting_value FROM contribution_settings WHERE setting_name = %s"
                cursor.execute(sql, (setting_name,))
                result = cursor.fetchone()
                
                if result:
                    return result['setting_value']
                return default_value
        except Exception as e:
            print(f"Error retrieving setting '{setting_name}': {str(e)}")
            return default_value
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def update_setting(setting_name, setting_value, description=None):
        """Update a setting value or insert if it doesn't exist"""
        conn = None
        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                # Check if setting exists
                cursor.execute("SELECT * FROM contribution_settings WHERE setting_name = %s", (setting_name,))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing setting
                    if description:
                        sql = """
                            UPDATE contribution_settings 
                            SET setting_value = %s, setting_description = %s 
                            WHERE setting_name = %s
                        """
                        cursor.execute(sql, (setting_value, description, setting_name))
                    else:
                        sql = "UPDATE contribution_settings SET setting_value = %s WHERE setting_name = %s"
                        cursor.execute(sql, (setting_value, setting_name))
                else:
                    # Insert new setting
                    sql = """
                        INSERT INTO contribution_settings (setting_name, setting_value, setting_description)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(sql, (setting_name, setting_value, description or ''))
                
                conn.commit()
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error updating setting '{setting_name}': {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_all_settings():
        """Get all settings as a dictionary"""
        conn = None
        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='V0sp0r0si968!',
                database='sml',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM contribution_settings ORDER BY setting_name")
                results = cursor.fetchall()
                
                settings = {}
                for row in results:
                    settings[row['setting_name']] = row
                
                return settings
        except Exception as e:
            print(f"Error retrieving all settings: {str(e)}")
            return {}
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_contribution_settings():
        """Get employer and employee contribution percentages"""
        employer_contrib = float(ContributionSettings.get_setting('employer_contribution_percentage', 13.0))
        employee_contrib = float(ContributionSettings.get_setting('employee_contribution_percentage', 8.0))
        
        return {
            'employer_contribution_percentage': employer_contrib,
            'employee_contribution_percentage': employee_contrib
        } 