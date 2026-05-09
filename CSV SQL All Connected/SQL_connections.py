import psycopg2
import pymysql
import oracledb

class SQLConnections:
    def __init__(self):
        self.connections = {}
        self.configs = {}

    def connect_postgres(self, host, db, user, password, port=5432):
        try:
            config = {
                "host": host,
                "database": db,
                "user": user,
                "password": password,
                "port": port
            }
            conn = psycopg2.connect(**config)
            self.connections["PostgreSQL"] = conn
            self.configs["PostgreSQL"] = config
            return conn
        except Exception as e:
            print("PostgreSQL connection error:", e)
            return None

    def connect_mysql(self, host, db, user, password, port=3306):
        try:
            config = {
                "host": host,
                "database": db,
                "user": user,
                "password": password,
                "port": port
            }
            conn = pymysql.connect(**config)
            self.connections["MySQL"] = conn
            self.configs["MySQL"] = config
            return conn
        except Exception as e:
            print("MySQL connection error:", e)
            return None

    def connect_oracle(self, host, db, user, password, port=1521):
        try:
            dsn = oracledb.makedsn(host, port, service_name=db)
            config = {
                "user": user,
                "password": password,
                "dsn": dsn
            }
            conn = oracledb.connect(**config)
            self.connections["Oracle"] = conn
            self.configs["Oracle"] = {
                "host": host,
                "database": db,
                "user": user,
                "password": password,
                "port": port
            }
            return conn
        except Exception as e:
            print("Oracle connection error:", e)
            return None

    def reconnect_postgres(self):
        config = self.configs.get("PostgreSQL")
        if not config:
            return None
        try:
            conn = psycopg2.connect(**config)
            self.connections["PostgreSQL"] = conn
            return conn
        except Exception as e:
            print("PostgreSQL reconnection failed:", e)
            return None

    def reconnect_mysql(self):
        config = self.configs.get("MySQL")
        if not config:
            return None
        try:
            conn = pymysql.connect(**config)
            self.connections["MySQL"] = conn
            return conn
        except Exception as e:
            print("MySQL reconnection failed:", e)
            return None

    def reconnect_oracle(self):
        config = self.configs.get("Oracle")
        if not config:
            return None
        try:
            dsn = oracledb.makedsn(
                config["host"],
                config["port"],
                service_name=config["database"]
            )
            conn = oracledb.connect(
                user=config["user"],
                password=config["password"],
                dsn=dsn
            )
            self.connections["Oracle"] = conn
            return conn
        except Exception as e:
            print("Oracle reconnection failed:", e)
            return None

    def get_connection(self, db_type):
        return self.connections.get(db_type)

    def close(self):
        for conn in self.connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self.connections.clear()