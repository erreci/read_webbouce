import logging
#import mariadb as db
import mysql.connector as db
  
import sys

class Database:
    """Class used to connect to the MySql Database"""
    __connection = None
    __cursor = None

    @classmethod
    def connect(cls, username, password, database, host, port):
        """Private method used to get a connection to the database"""
        try:
            cls.__connection = db.connect(
                user=username, password=password, database=database, host=host, port=int(port))
            cls.__connection.autocommit = False
            cls.__cursor = cls.__connection.cursor()
            return True
        except:
            logging.exception("Failed to connect!")
            cls.__connection = None
            cls.__cursor = None
            return False

    @classmethod
    def execute(cls, sql, params=None):
        """Method used to execute queries"""
        try:
            cls.__cursor.execute(sql, params or ())
            return cls.__cursor.lastrowid
        except:
            logging.exception("Failed to execute query!")
            return False
            
    @classmethod
    def fetchall(cls):
        """Method used to get results from a query"""
        try:
            return cls.__cursor.fetchall()
        except:
            logging.exception("Failed to execute fetchall!")
            return False

    @classmethod
    def commit(cls):
        """Method used to commit all the queries"""
        try:
            cls.__connection.commit()
            return True
        except:
            logging.exception("Failed to commit!")
            return False

    @classmethod
    def close(cls):
        """Method used to close the databse connection"""
        cls.__connection.close()

    @classmethod
    def rowcount(cls):
        """ get row count"""
        return cls.__cursor.rowcount
