from __future__ import annotations

import mysql.connector
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import cv2


BBox = Tuple[int, int, int, int]


@dataclass
class FineCandidate:
    frame: any
    frame_idx: int
    rider_bbox: BBox
    plate_bbox: BBox
    no_helmet_conf: float
    plate_conf: float
    overall_conf: float


class FineCaseStore:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.base_dir = (project_root / "outputs" / "predictions" / "fine_case").resolve()
        self.person_dir = self.base_dir / "person"
        self.plate_dir = self.base_dir / "plate"
        self.person_dir.mkdir(parents=True, exist_ok=True)
        self.plate_dir.mkdir(parents=True, exist_ok=True)
        
        # MariaDB connection config
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "root",
            "database": "helm_detect"
        }

    def _get_connection(self):
        return mysql.connector.connect(**self.db_config)

    @staticmethod
    def _clamp_bbox(bbox: BBox, width: int, height: int) -> BBox:
        x1, y1, x2, y2 = bbox
        x1 = max(0, min(int(x1), width - 1))
        y1 = max(0, min(int(y1), height - 1))
        x2 = max(1, min(int(x2), width))
        y2 = max(1, min(int(y2), height))
        return x1, y1, x2, y2

    def save_case(self, candidate: FineCandidate, source: str) -> Optional[int]:
        frame = candidate.frame
        height, width = frame.shape[:2]

        rx1, ry1, rx2, ry2 = self._clamp_bbox(candidate.rider_bbox, width, height)
        px1, py1, px2, py2 = self._clamp_bbox(candidate.plate_bbox, width, height)

        person_crop = frame[ry1:ry2, rx1:rx2]
        plate_crop = frame[py1:py2, px1:px2]
        if person_crop.size == 0 or plate_crop.size == 0:
            return None

        ts_file = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        person_path = str((self.person_dir / f"person_{ts_file}.jpg").resolve())
        plate_path = str((self.plate_dir / f"plate_{ts_file}.jpg").resolve())
        cv2.imwrite(person_path, person_crop)
        cv2.imwrite(plate_path, plate_crop)

        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO fine_cases
            (ts, source, status, overall_conf, no_helmet_conf, plate_conf, plate_number, frame_idx, person_path, plate_path)
            VALUES (%s, %s, 'fine_pending', %s, %s, %s, 'ID REQUIRED', %s, %s, %s)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                str(source),
                float(candidate.overall_conf),
                float(candidate.no_helmet_conf),
                float(candidate.plate_conf),
                int(candidate.frame_idx),
                person_path,
                plate_path,
            ),
        )
        row_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return row_id

    def assign_fine(self, person_id: int, case_id: int) -> bool:
        # Business Logic: Scaled fining (500, 1000, 1500...)
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT violation_count FROM government_records WHERE id = %s", (int(person_id),))
        res = cur.fetchone()
        if not res:
            cur.close()
            conn.close()
            return False
            
        new_fine_amt = 500 * (res[0] + 1)
        
        cur.execute("""
            UPDATE government_records 
            SET violation_count = violation_count + 1, total_fine_due = total_fine_due + %s
            WHERE id = %s
        """, (new_fine_amt, int(person_id)))
        
        cur.execute("UPDATE fine_cases SET status = 'fine_closed' WHERE id = %s", (int(case_id),))
        
        conn.commit()
        cur.close()
        conn.close()
        return True

    def close_case(self, case_id: int) -> bool:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE fine_cases
            SET status = 'fine_closed'
            WHERE id = %s AND status = 'fine_pending'
            """,
            (int(case_id),),
        )
        changed = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return changed

    def get_pending_cases(self, limit: int = 500, search_query: Optional[str] = None, date_filter: Optional[str] = None) -> List[Dict]:
        conn = self._get_connection()
        cur = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM fine_cases WHERE status = 'fine_pending'"
        params = []
        
        if search_query:
            # Check if it's an ID search (#123 or 123) or a plate search
            clean_search = search_query.replace("#", "").strip()
            if clean_search.isdigit():
                query += " AND id = %s"
                params.append(int(clean_search))
            else:
                query += " AND plate_number LIKE %s"
                params.append(f"%{search_query}%")
        
        if date_filter:
            query += " AND DATE(ts) = %s"
            params.append(date_filter)
            
        query += " ORDER BY id DESC LIMIT %s"
        params.append(int(limit))
        
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def get_all_records(self, search_query: Optional[str] = None) -> List[Dict]:
        conn = self._get_connection()
        cur = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM government_records"
        params = []
        
        if search_query:
            query += " WHERE plate_number LIKE %s OR person_name LIKE %s"
            params.append(f"%{search_query}%")
            params.append(f"%{search_query}%")
            
        query += " ORDER BY person_name ASC"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
