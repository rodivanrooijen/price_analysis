import mysql.connector.cursor_cext
import mysql.connector


class CursorMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class MyCursor(metaclass=CursorMeta):
    def __init__(
        self, host: str = "localhost", user: str = "root", password: str = ""
    ) -> None:
        self.mydb: mysql.connector.connection_cext.CMySQLConnection = (
            mysql.connector.connect(
                host=host,
                user=user,
                password=password,
            )
        )

    def get_mydb(self) -> mysql.connector.connection_cext.CMySQLConnection:
        return self.mydb

    def get_mycursor(self) -> mysql.connector.cursor_cext.CMySQLCursor:
        return self.mydb.cursor()


# export AZURE_SQL_CONNECTIONSTRING='Driver={ODBC Driver 18 for SQL Server};Server=tcp:yc2401data.database.windows.net,1433;Database=hotel;Uid=proefaccount@infocodefounders.onmicrosoft.com ;Pwd=uiop7890UIOP&*();Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'
