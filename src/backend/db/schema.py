"""PostgreSQL schema initialisation — creates the database and tables if they don't exist."""
from __future__ import annotations

import psycopg2
from psycopg2 import sql
from psycopg2.errors import DuplicateDatabase

DB_NAME = "helm_detect"


class HelmDB:
    """Utility class that bootstraps the PostgreSQL database and tables on first run."""

    def __init__(self, database: str = DB_NAME) -> None:
        self.database = database
        self._init_db()

    def _connect(self, use_db: bool = True) -> psycopg2.extensions.connection:
        dbname = self.database if use_db else "postgres"
        return psycopg2.connect(dbname=dbname)

    def _init_db(self) -> None:
        # Create the database if it doesn't exist
        conn = self._connect(use_db=False)
        conn.autocommit = True
        cur = conn.cursor()
        try:
            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database))
            )
        except DuplicateDatabase:
            pass
        finally:
            cur.close()
            conn.close()

        # Create tables
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fine_cases (
                id             SERIAL PRIMARY KEY,
                ts             TIMESTAMP    NOT NULL,
                source         VARCHAR(255) NOT NULL,
                status         VARCHAR(50)  DEFAULT 'fine_pending',
                overall_conf   FLOAT        NOT NULL,
                no_helmet_conf FLOAT        NOT NULL,
                plate_conf     FLOAT        NOT NULL,
                plate_number   VARCHAR(50)  DEFAULT 'ID REQ',
                frame_idx      INT          NOT NULL,
                person_path    VARCHAR(512),
                plate_path     VARCHAR(512)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS government_records (
                id              SERIAL PRIMARY KEY,
                plate_number    VARCHAR(50)  UNIQUE NOT NULL,
                person_name     VARCHAR(255) NOT NULL,
                license_no      VARCHAR(100),
                contact         VARCHAR(100),
                address         VARCHAR(255),
                violation_count INT DEFAULT 0,
                total_fine_due  INT DEFAULT 0
            )
            """
        )
        conn.commit()
        cur.close()
        conn.close()


if __name__ == "__main__":
    HelmDB()
    print("Database initialised successfully.")
