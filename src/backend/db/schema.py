import psycopg2
from psycopg2 import sql
from psycopg2.errors import DuplicateDatabase

from backend.config import DB_NAME


class HelmDB:
    def __init__(self, database: str = DB_NAME):
        self.database = database
        self._init_db()

    def _get_connection(self, include_db: bool = True):
        dbname = self.database if include_db else "postgres"
        return psycopg2.connect(dbname=dbname)

    def _init_db(self):
        conn = self._get_connection(include_db=False)
        conn.autocommit = True
        cursor = conn.cursor()
        try:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database)))
        except DuplicateDatabase:
            pass
        finally:
            cursor.close()
            conn.close()

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fine_cases (
                id SERIAL PRIMARY KEY,
                ts TIMESTAMP NOT NULL,
                source VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'fine_pending',
                overall_conf FLOAT NOT NULL,
                no_helmet_conf FLOAT NOT NULL,
                plate_conf FLOAT NOT NULL,
                plate_number VARCHAR(50) DEFAULT 'ID REQ',
                frame_idx INT NOT NULL,
                person_path VARCHAR(512),
                plate_path VARCHAR(512)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS government_records (
                id SERIAL PRIMARY KEY,
                plate_number VARCHAR(50) UNIQUE NOT NULL,
                person_name VARCHAR(255) NOT NULL,
                license_no VARCHAR(100),
                contact VARCHAR(100),
                address VARCHAR(255),
                violation_count INT DEFAULT 0,
                total_fine_due INT DEFAULT 0
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()


if __name__ == "__main__":
    HelmDB()
