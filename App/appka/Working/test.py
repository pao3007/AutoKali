from datetime import datetime


class DatabaseCom:

    import pyodbc as pyodbc

    sylexIsysConnectionString = {
        # 'InitialCatalog': 'ISYS',
        # 'DataSource': 'SYXDBX02\\ISYS',
        'InitialCatalog': 'ISYS',
        'DataSource': 'SYXDBX02\\ISYS',
        'UserID': 'peaklogger',
        'Password': 'peaklogger123',
        'IntegratedSecurity': False,
        'MultipleActiveResultSets': True,
        'PersistSecurityInfo': True,
        'ConnectTimeout': 1
    }

    integrated_security = 'True' if sylexIsysConnectionString['IntegratedSecurity'] else 'False'
    mars = 'True' if sylexIsysConnectionString['MultipleActiveResultSets'] else 'False'
    persist_security_info = 'True' if sylexIsysConnectionString['PersistSecurityInfo'] else 'False'

    conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};" \
               f"SERVER={sylexIsysConnectionString['DataSource']};" \
               f"DATABASE={sylexIsysConnectionString['InitialCatalog']};" \
               f"UID={sylexIsysConnectionString['UserID']};" \
               f"PWD={sylexIsysConnectionString['Password']};" \
               f"Integrated Security={integrated_security};" \
               f"MultipleActiveResultSets={mars};" \
               f"Persist Security Info={persist_security_info};" \
               f"Connect Timeout={sylexIsysConnectionString['ConnectTimeout']};"
    conn_str += ";TrustServerCertificate=yes;Encrypt=no"

    def __init__(self):
        self.load_sylex_nominal_wavelength(245203)
        par = ["TEST", "TEST", "TEST2", 99, 99, 1, 1111.9999, 1999.0, 1999.0, 99.0, 99.99, 9.99, "TEST", "TEST", 90.9, 99.9,
               "TEST"]
        current_datetime = datetime.now()

        # Format the datetime object to a string
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        par.append(formatted_datetime)
        par.append("TESTER")
        # self.export_to_dabase(par)
        # self.fetch_records_by_sylexsn("TEST1")

    def export_to_dabase(self, params):
        query = '''INSERT INTO tblKalibracia_Accel (SylexON, Customer, SylexSN, ErrorCount, CalibrationNumber, 
        CalibrationFinal, Sensitivity, CWL1, CWL2, Flatness, Offset, Asymmetry, RawDataLocation, CalibrationProfile, 
        TempCoef1, TempCoef2, Notes, Timestamp, Operator) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
        ?, ?)'''
        cal_num = self.fetch_records_by_sylexsn(params[2])
        if cal_num == 0:
            params[4] = 0
        elif len(cal_num) >= 1:
            self.set_last_calibration_old(params[2])
            params[4] = int(cal_num[5]) + 1
        try:
            conn = self.pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            conn.close()
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

    def fetch_records_by_sylexsn(self, sylexsn_value):
        query = """
            SELECT TOP 1 *
            FROM tblKalibracia_Accel
            WHERE SylexSN = ?
            ORDER BY Id DESC
            """

        try:
            conn = self.pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(query, sylexsn_value)
            rows = cursor.fetchone()
            cursor.close()
            conn.close()
            if rows:
                print(rows)
                return rows
            return 0
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

    def set_last_calibration_old(self, s_n):
        query = """
        UPDATE tblKalibracia_Accel
        SET CalibrationFinal=0
        WHERE SylexSN = ? AND CalibrationFinal=1
        """

        try:
            conn = self.pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(query, s_n)
            conn.commit()
            cursor.close()
            conn.close()
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

    def load_sylex_nominal_wavelength(self, objednavka_id):
        query = """
        SELECT 
            [Zákazky].[ID] AS [Zakazka], 
            [Výrobky].[ID] AS [Objednavka], 
            [Výrobky].[Množstvo], 
            [Výrobky].[Popis], 
            [Zákazky].[Divízia], 
            [Zákazky].[Obchodné meno] AS [Zakaznik], 
            [Výrobky].[Sensor] 
        FROM 
            [Zákazky] 
        INNER JOIN 
            [Výrobky] ON [Zákazky].[ID] = [Výrobky].[IDZákazky] 
        LEFT OUTER JOIN 
            [ČíselníkNálepky] ON [Výrobky].[ČíselníkNálepkyID] = [ČíselníkNálepky].[ID] 
        LEFT OUTER JOIN 
            [VýrobkyNálepky] ON [Výrobky].[ID] = [VýrobkyNálepky].[VýrobkyID] 
        WHERE 
            [Výrobky].[ID] = ?
        """
        try:
            conn = self.pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(query, objednavka_id)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

        if row:
            print(row)
            return self.extract_wavelengths(row)
        return 0

    def extract_wavelengths(self, arr):
        import re
        # Pattern now includes option for a comma or dot as decimal separator
        pattern = r'WL:\s*([\d]+([.,]\d+)?[\/\-_][\d]+([.,]\d+)?)nm'

        for item in arr:
            s = str(item)
            match = re.search(pattern, s)

            if match:
                extracted_numbers = re.split(r'[\/\-_]', match.group(1))
                # Replace comma with dot for float conversion
                extracted_numbers = [x.replace(',', '.') for x in extracted_numbers]

                return list(map(float, extracted_numbers))
        return None


DatabaseCom()


