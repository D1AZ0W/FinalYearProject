import mysql.connector

class HelmDB:
    def __init__(self, host="localhost", user="root", password="root", database="helm_detect"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self._init_db()

    def _get_connection(self, include_db=True):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database if include_db else None
        )

    def _init_db(self):
        # Create database if not exists
        conn = self._get_connection(include_db=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        cursor.close()
        conn.close()

        # Create tables
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Fine Cases Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fine_cases (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ts DATETIME NOT NULL,
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

        # 2. Government Records Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS government_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
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
