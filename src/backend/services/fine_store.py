"""Fine case persistence — saving violation images and DB records."""
from __future__ import annotations

import psycopg2
import psycopg2.extras
import psycopg2.pool
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import cv2

BBox = Tuple[int, int, int, int]


@dataclass
class FineCandidate:
    """Holds a single detected violation before it is committed to the DB."""
    frame: Any          # numpy ndarray
    frame_idx: int
    rider_bbox: BBox
    plate_bbox: BBox
    no_helmet_conf: float
    plate_conf: float
    overall_conf: float


class FineCaseStore:
    """Saves violation images to disk and records to PostgreSQL.

    Uses a ThreadedConnectionPool so the detection thread and Flask request
    threads share a fixed pool of connections instead of opening a new
    connection on every operation.
    """

    _MIN_CONN = 2
    _MAX_CONN = 10
    DB_CONFIG = {"dbname": "helm_detect"}

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.base_dir = (project_root / "outputs" / "predictions" / "fine_case").resolve()
        self.person_dir = self.base_dir / "person"
        self.plate_dir  = self.base_dir / "plate"
        self.person_dir.mkdir(parents=True, exist_ok=True)
        self.plate_dir.mkdir(parents=True, exist_ok=True)

        self._pool = psycopg2.pool.ThreadedConnectionPool(
            self._MIN_CONN, self._MAX_CONN, **self.DB_CONFIG
        )

    @contextmanager
    def _conn(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Borrow a connection from the pool; commit on success, rollback on error."""
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            # Always return connection to the pool, even on early return/exception
            self._pool.putconn(conn)

    @staticmethod
    def _clamp_bbox(bbox: BBox, width: int, height: int) -> BBox:
        x1, y1, x2, y2 = bbox
        return (
            max(0, min(int(x1), width - 1)),
            max(0, min(int(y1), height - 1)),
            max(1, min(int(x2), width)),
            max(1, min(int(y2), height)),
        )

    def save_case(self, candidate: FineCandidate, source: str) -> Optional[int]:
        """Crop + save images and insert a fine_cases row. Returns the new row id."""
        frame = candidate.frame
        h, w = frame.shape[:2]

        rx1, ry1, rx2, ry2 = self._clamp_bbox(candidate.rider_bbox, w, h)
        px1, py1, px2, py2 = self._clamp_bbox(candidate.plate_bbox, w, h)

        person_crop = frame[ry1:ry2, rx1:rx2]
        plate_crop  = frame[py1:py2, px1:px2]
        if person_crop.size == 0 or plate_crop.size == 0:
            return None

        ts_tag      = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        person_path = str((self.person_dir / f"person_{ts_tag}.jpg").resolve())
        plate_path  = str((self.plate_dir  / f"plate_{ts_tag}.jpg").resolve())
        cv2.imwrite(person_path, person_crop)
        cv2.imwrite(plate_path,  plate_crop)

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO fine_cases
                      (ts, source, status, overall_conf, no_helmet_conf, plate_conf,
                       plate_number, frame_idx, person_path, plate_path)
                    VALUES (%s, %s, 'fine_pending', %s, %s, %s, 'ID REQUIRED', %s, %s, %s)
                    RETURNING id
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
                row_id = cur.fetchone()[0]
        return row_id

    def assign_fine(self, person_id: int, case_id: int) -> bool:
        """Link a government_records person to a fine_cases row.
        Fine amount is computed atomically in SQL to avoid race conditions.
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM government_records WHERE id = %s",
                    (person_id,),
                )
                if not cur.fetchone():
                    return False

                cur.execute(
                    """
                    UPDATE government_records
                    SET violation_count = violation_count + 1,
                        total_fine_due  = total_fine_due + 500 * (violation_count + 1)
                    WHERE id = %s
                    """,
                    (person_id,),
                )
                cur.execute(
                    "UPDATE fine_cases SET status = 'fine_closed' WHERE id = %s",
                    (case_id,),
                )
        return True

    def close_case(self, case_id: int) -> bool:
        """Mark a pending case as closed without assigning a fine."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE fine_cases
                    SET status = 'fine_closed'
                    WHERE id = %s AND status = 'fine_pending'
                    """,
                    (case_id,),
                )
                return cur.rowcount > 0

    def get_pending_cases(
        self,
        limit: int = 500,
        search_query: Optional[str] = None,
        date_filter: Optional[str] = None,
    ) -> List[Dict]:
        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query  = "SELECT * FROM fine_cases WHERE status = 'fine_pending'"
                params: list = []

                if search_query:
                    clean = search_query.replace("#", "").strip()
                    if clean.isdigit():
                        query += " AND id = %s"
                        params.append(int(clean))
                    else:
                        query += " AND plate_number ILIKE %s"
                        params.append(f"%{search_query}%")

                if date_filter:
                    query += " AND DATE(ts) = %s"
                    params.append(date_filter)

                query += " ORDER BY id DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)
                return [dict(r) for r in cur.fetchall()]

    def get_all_records(self, search_query: Optional[str] = None) -> List[Dict]:
        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query  = "SELECT * FROM government_records"
                params: list = []

                if search_query:
                    query += " WHERE plate_number ILIKE %s OR person_name ILIKE %s"
                    params.extend([f"%{search_query}%", f"%{search_query}%"])

                query += " ORDER BY person_name ASC"
                cur.execute(query, params)
                return [dict(r) for r in cur.fetchall()]
