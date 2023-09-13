class DatabaseCom:

    import pyodbc as pyodbc

    sylexIsysConnectionString = {
        'DataSource': 'SYXDBX02\\ISYS',
        'UserID': 'peaklogger',
        'Password': 'peaklogger123',
        'IntegratedSecurity': False,
        'MultipleActiveResultSets': True,
        'PersistSecurityInfo': True,
        'ConnectTimeout': 1
    }

    def do_connection_string(self, database):
        integrated_security = 'True' if self.sylexIsysConnectionString['IntegratedSecurity'] else 'False'
        mars = 'True' if self.sylexIsysConnectionString['MultipleActiveResultSets'] else 'False'
        persist_security_info = 'True' if self.sylexIsysConnectionString['PersistSecurityInfo'] else 'False'

        conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};" \
                   f"SERVER={self.sylexIsysConnectionString['DataSource']};" \
                   f"DATABASE={database};" \
                   f"UID={self.sylexIsysConnectionString['UserID']};" \
                   f"PWD={self.sylexIsysConnectionString['Password']};" \
                   f"Integrated Security={integrated_security};" \
                   f"MultipleActiveResultSets={mars};" \
                   f"Persist Security Info={persist_security_info};" \
                   f"Connect Timeout={self.sylexIsysConnectionString['ConnectTimeout']};"
        conn_str += ";TrustServerCertificate=yes;Encrypt=no"
        return conn_str

    def export_to_database(self, params):
        try:
            conn_str = self.do_connection_string("DBFOS")
            query = '''INSERT INTO tblKalibracia_Accel (SylexON, Customer, ProductDescription, SensorName, 
            SylexSN, ErrorCount, CalibrationNumber, CalibrationFinal, Sensitivity, CWL1, CWL2, Flatness, Offset, 
            Asymmetry, RawDataLocation, CalibrationProfile, TempCoef1, TempCoef2, Notes, Timestamp, Operator, Evaluation) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
            ?, ?)'''
            cal_num = self.fetch_records_by_sylexsn(params[2], conn_str)
            if cal_num == 0:
                params[4] = 0
            elif len(cal_num) >= 1:
                self.set_last_calibration_old(params[2])
                params[4] = int(cal_num[5]) + 1
            print(params)
        except Exception:
            return -2
        try:
            conn = self.pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            conn.close()
            return 0
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

    def update_export_note(self, s_n, notes):
        conn_str = self.do_connection_string("DBFOS")
        query = "UPDATE tblKalibracia_Accel SET Notes = ? WHERE SylexSN = ? AND CalibrationFinal = 1"
        try:
            conn = self.pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute(query, (notes, s_n))
            conn.commit()
            cursor.close()
            conn.close()
            return 1
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

    def fetch_records_by_sylexsn(self, sylexsn_value, conn_str):
        query = """
            SELECT TOP 1 *
            FROM tblKalibracia_Accel
            WHERE SylexSN = ?
            ORDER BY Id DESC
            """

        try:
            conn = self.pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute(query, sylexsn_value)
            rows = cursor.fetchone()
            cursor.close()
            conn.close()
            if rows:
                return rows
            return 0
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

    def set_last_calibration_old(self, s_n):
        conn_str = self.do_connection_string("DBFOS")
        query = """
        UPDATE tblKalibracia_Accel
        SET CalibrationFinal=0
        WHERE SylexSN = ? AND CalibrationFinal=1
        """

        try:
            conn = self.pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute(query, s_n)
            conn.commit()
            cursor.close()
            conn.close()
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

    def load_sylex_nominal_wavelength(self, objednavka_id, all_info=False):
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
            conn = self.pyodbc.connect(self.do_connection_string("ISYS"))
            cursor = conn.cursor()
            cursor.execute(query, objednavka_id)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except self.pyodbc.Error as e:
            print("Error connecting to the database:", e)
            return -1

        if row:
            if all_info:
                return row
            else:
                return self.extract_wavelengths(row)
        return 0

    def extract_wavelengths(self, arr):
        import re
        pattern = r'WL:\s*([\d]+[\/\-_][\d]+)nm'

        for item in arr:
            s = str(item)
            match = re.search(pattern, s)
            if match:
                return list(map(int, re.split(r'[\/\-_]', match.group(1))))
        return None
