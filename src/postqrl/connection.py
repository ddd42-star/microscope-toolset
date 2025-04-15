import os
import logging
from typing import Optional
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class DBConnection:
    def __init__(self, db_host: Optional[str] = None, db_name: Optional[str] = None, db_user: Optional[str] = None,
                 db_password: Optional[str] = None, db_port: Optional[int] = None):

        # assign it
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_port = db_port

        if db_host is None:
            load_dotenv()
            try:
                self.db_host = os.getenv("DB_HOST")
            except Exception as e:
                raise ValueError(e)
        if db_name is None:
            load_dotenv()
            try:
                self.db_name = os.getenv("DB_NAME")
            except Exception as e:
                raise ValueError(e)
        if db_user is None:
            load_dotenv()
            try:
                self.db_user = os.getenv("DB_USER")
            except Exception as e:
                raise ValueError(e)
        if db_password is None:
            load_dotenv()
            try:
                self.db_password = os.getenv("DB_PASSWORD")
            except Exception as e:
                raise ValueError(e)
        if db_port is None:
            load_dotenv()
            try:
                self.db_port = int(os.getenv("DB_PORT"))
            except Exception as e:
                raise ValueError(e)


        print(self.db_port,self.db_password,self.db_user,self.db_name, self.db_host)

        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=2,
            maxconn=30,
            host=self.db_host,
            user=self.db_user,
            database=self.db_name,
            password=self.db_password,
            port=self.db_port)

    def get_connect(self):
        return self.pool.getconn()

    def put_connect(self, connection):
        self.pool.putconn(connection)

    def disconnect(self):
        self.pool.closeall()