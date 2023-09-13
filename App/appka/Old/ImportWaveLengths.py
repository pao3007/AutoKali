class ImportWaveLengths:

    import pyodbc as pyodbc

    sylexIsysConnectionString = {
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
        conn = self.pyodbc.connect(self.conn_str)
        cursor = conn.cursor()
        cursor.execute(query, objednavka_id)
        row = cursor.fetchone()

        if row:
            return self.extract_wavelengths(row)
        return None

    def extract_wavelengths(self, arr):
        import re
        pattern = r'WL:\s*([\d]+[\/\-_][\d]+)nm'

        for item in arr:
            s = str(item)
            match = re.search(pattern, s)
            if match:
                return list(map(int, re.split(r'[\/\-_]', match.group(1))))

        return None


    S_N = '242358'


clas = ImportWaveLengths().load_sylex_nominal_wavelength("242358")
print(clas)





