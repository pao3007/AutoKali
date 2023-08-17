import re
import decimal

import pyodbc as pyodbc

class SylexNominalWavelength:
    def __init__(self, KodMaterialu, Objednavka, Popis):
        self.KodMaterialu = KodMaterialu
        self.Objednavka = Objednavka
        self.Popis = Popis

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

def sylex_vyrobok_decode_wavelengths(wavelengths, dbfos=False, constant1500=True):
    try:
        decoded = []

        if wavelengths:
            if not dbfos:
                if "WL:" in wavelengths:
                    WLmatchList = re.findall(r'WL:(.+?);', wavelengths)
                    print(WLmatchList)
                    wavelengths = ''.join(WLmatchList)
                else:
                    return decoded

            basePart = ""
            matchList = re.findall(r'(\d+(\.\d+))|(\d+(\,\d+)?)', wavelengths)

            for match in matchList:
                for capture in match:
                    value = capture.replace(',', '.')
                    if value:
                        valueDecimal = decimal.Decimal(value)
                        integralPart = int(valueDecimal)

                        if len(str(integralPart)) == 2:
                            valueDecimal = decimal.Decimal(basePart + value)
                            if not constant1500:
                                while valueDecimal < decoded[-1]:
                                    basePart = str(decimal.Decimal(basePart) + 1)
                                    valueDecimal = decimal.Decimal(basePart + value)
                        elif len(decoded) == 0:
                            basePart = value[:2]

                        decoded.append(valueDecimal)

        decoded.sort()
        print("TWO")
        return decoded

    except Exception as ex:
        raise Exception(f"Could not parse {wavelengths}") from ex

def load_sylex_nominal_wavelength(objednavka_id):
    # query = """
    # SELECT ČíselníkMateriál.KódMateriálu, Výrobky.ID, ČíselníkMateriál.Popis
    # FROM Výrobky
    # INNER JOIN VýrobkyMateriál ON Výrobky.ID = VýrobkyMateriál.IdVýrobku
    # INNER JOIN ČíselníkMateriál ON VýrobkyMateriál.IdMateriálu = ČíselníkMateriál.ID
    # WHERE (Výrobky.ID = ?)
    # AND (
    #     ČíselníkMateriál.Popis LIKE N'M;%'
    #     OR ČíselníkMateriál.Popis LIKE N'D;%'
    #     OR ČíselníkMateriál.Popis LIKE N'S;%'
    #     OR ČíselníkMateriál.Popis LIKE N'SG%'
    # )
    # """

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
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(query, objednavka_id)

    row = cursor.fetchone()
    print(row)
    if row:
        return SylexNominalWavelength(
            KodMaterialu=row[0],
            Objednavka=row[1],
            Popis=row[2]
        )

    return None

try:
    out = load_sylex_nominal_wavelength('242358')

    print("Connected successfully!")

    # Query to get all tables
    # query = "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';"
    #
    # cursor = connection.cursor()
    # cursor.execute(query)
    #
    # tables = cursor.fetchall()
    # for table in tables:
    #     print(f"{table.TABLE_SCHEMA}.{table.TABLE_NAME}")
    #
    # connection.close()
except Exception as e:
    print(f"Failed to connect: {e}")

print(sylex_vyrobok_decode_wavelengths(out.Popis))




