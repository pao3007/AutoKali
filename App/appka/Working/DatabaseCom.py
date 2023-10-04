from yaml import safe_load
from os import path


class DatabaseCom:

    import pyodbc as pyodbc

    def __init__(self, start_folder):
        filename = path.join(start_folder, "database_com.yaml")
        with open(filename, 'r', encoding="utf-8") as file:
            self.database_conf = safe_load(file)

    # sylexIsysConnectionString = {
    #     'DataSource': 'SYXDBX02\\ISYS',
    #     'UserID': 'peaklogger',
    #     'Password': 'peaklogger123',
    #     'IntegratedSecurity': False,
    #     'MultipleActiveResultSets': True,
    #     'PersistSecurityInfo': True,
    #     'ConnectTimeout': 1
    # }

    def do_connection_string(self, database):
        try:
            integrated_security = 'True' if self.database_conf['ConnectionKey']['IntegratedSecurity'] else 'False'
            mars = 'True' if self.database_conf['ConnectionKey']['MultipleActiveResultSets'] else 'False'
            persist_security_info = 'True' if self.database_conf['ConnectionKey']['PersistSecurityInfo'] else 'False'
            conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};" \
                       f"SERVER={str(self.database_conf['ConnectionKey']['DataSource'])};" \
                       f"DATABASE={str(database)};" \
                       f"UID={str(self.database_conf['ConnectionKey']['UserID'])};" \
                       f"PWD={str(self.database_conf['ConnectionKey']['Password'])};" \
                       f"Integrated Security={integrated_security};" \
                       f"MultipleActiveResultSets={mars};" \
                       f"Persist Security Info={persist_security_info};" \
                       f"Connect Timeout={str(self.database_conf['ConnectionKey']['ConnectTimeout'])};"
            conn_str += ";TrustServerCertificate=yes;Encrypt=no"
            return conn_str
        except Exception as e:
            print("do_connection_string:", e)

    def export_to_database(self, params):
        print("EXPORT TO DATABASE")
        try:
            conn_str = self.do_connection_string(self.database_conf['ExportDatabase'])
            query = '''INSERT INTO tblKalibracia_Accel (SylexON, Customer,
            SylexSN, ErrorCount, CalibrationNumber, CalibrationFinal, Sensitivity, CWL1, CWL2, Flatness, Offset,
            Asymmetry, RawDataLocation, CalibrationProfile, TempCoef1, TempCoef2, Notes, Timestamp, Operator,
            ProductDescription, SensorName, Evaluation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?)'''
            query = self.database_conf['ExportToDatabaseAcc']
            cal_num = self.fetch_records_by_sylexsn(params[2], conn_str)
            if cal_num == 0:
                params[4] = 0
            elif len(cal_num) >= 1:
                self.set_last_calibration_old(params[2])
                params[4] = int(cal_num[5]) + 1
            print(params)
        except Exception as e:
            print(f"export_to_database1:{e}")
            return -2
        try:
            conn = self.pyodbc.connect(conn_str)
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
            conn.close()
            return 0
        except Exception as e:
            print("export_to_database2:", e)
            return -1

    def update_export_note(self, s_n, notes):
        print("NOTE TO DATABASE")
        conn_str = self.do_connection_string(self.database_conf['ExportDatabase'])
        query = "UPDATE tblKalibracia_Accel SET Notes = ? WHERE SylexSN = ? AND CalibrationFinal = 1"
        query = self.database_conf['ExportNoteAcc']
        try:
            conn = self.pyodbc.connect(conn_str)
            with conn.cursor() as cursor:
                cursor.execute(query, (notes, s_n))
                conn.commit()
            conn.close()
            return 1
        except self.pyodbc.Error as e:
            print("update_export_note:", e)
            return -1

    def fetch_records_by_sylexsn(self, sylexsn_value, conn_str):
        query = """
            SELECT TOP 1 *
            FROM tblKalibracia_Accel
            WHERE SylexSN = ?
            ORDER BY Id DESC
            """
        query = self.database_conf['FindMostRecentSN']

        try:
            conn = self.pyodbc.connect(conn_str)
            with conn.cursor() as cursor:
                cursor.execute(query, sylexsn_value)
                rows = cursor.fetchone()
            conn.close()
            if rows:
                return rows
            return 0
        except self.pyodbc.Error as e:
            print("fetch_records_by_sylexsn:", e)
            return -1

    def set_last_calibration_old(self, s_n):
        conn_str = self.do_connection_string(self.database_conf['ExportDatabase'])
        query = """
        UPDATE tblKalibracia_Accel
        SET CalibrationFinal=0
        WHERE SylexSN = ? AND CalibrationFinal=1
        """
        query = self.database_conf['UpdateFinalValues']
        try:
            conn = self.pyodbc.connect(conn_str)
            with conn.cursor() as cursor:
                cursor.execute(query, s_n)
                conn.commit()
            conn.close()
        except self.pyodbc.Error as e:
            print("set_last_calibration_old:", e)
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
        query = self.database_conf['GetWaveLengthQuery']
        try:

            database = self.database_conf['LoadWLDatabase']
            con_str = self.do_connection_string(database)
            conn = self.pyodbc.connect(con_str)
            with conn.cursor() as cursor:
                cursor.execute(query, objednavka_id)
                row = cursor.fetchone()
            conn.close()

            if row:
                if all_info:
                    return row
                else:
                    return self.extract_wavelengths(row)
            return 0

        except self.pyodbc.Error as e:
            print("load_sylex_nominal_wavelength:", e)
            return -1

    def extract_wavelengths(self, arr):
        import re
        pattern = r'WL:\s*([\d]+[\/\-_][\d]+)nm'
        try:
            for item in arr:
                s = str(item)
                match = re.search(pattern, s)
                if match:
                    return list(map(int, re.split(r'[\/\-_]', match.group(1))))
            return None
        except Exception as e:
            print("extract_wavelengths:", e)
            return -1
