import os
import urllib.parse


def db_connect():
    azure_host: str = os.environ.get("AZURE_SQL_HOST")
    azure_username: str = os.environ.get("AZURE_SQL_USERNAME")
    azure_password: str = os.environ.get("AZURE_SQL_PW")
    azure_database: str = os.environ.get("AZURE_SQL_DB")
    if (
        azure_host is None
        or azure_username is None
        or azure_password is None
        or azure_database is None
    ):
        raise ValueError("Enviroment variables not correctly set")
    return f"mysql+mysqlconnector://{azure_username}:{urllib.parse.quote_plus(azure_password)}@{azure_host}/{azure_database}"
