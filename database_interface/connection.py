__author__ = 'masslab'

from PyQt4.QtSql import QSqlDatabase
from nist_config import nist_db_usr, nist_db_pwd, nist_db_host_server, nist_db_schema


class Connect:
    """
    Creates a connection to the MySQL database. An instance of QSqlDatabase represents the connection.

    """
    def __init__(self):


        self.db = QSqlDatabase.addDatabase("QMYSQL")
        self.db.setHostName(nist_db_host_server)
        self.db.setDatabaseName(nist_db_schema)
        self.db.setUserName(nist_db_usr)
        self.db.setPassword(nist_db_pwd)
        self.db.open()


