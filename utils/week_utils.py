from datetime import datetime
from typing import Tuple
from contextlib import closing
from models.database import db, get_week_info

class WeekUtils:
    """Utility functions for week management"""
    
    @staticmethod
    def get_week_key(dt: datetime | None = None) -> Tuple[int, int]:
        """Get ISO year and week number for a given datetime"""
        dt = dt or datetime.now()
        iso_year, iso_week, _ = dt.isocalendar()
        return iso_year, iso_week
    
    @staticmethod
    def get_or_create_current_week() -> int:
        """Get or create the current week record and return its ID"""
        from os import environ
        default_quota = int(environ.get("DEFAULT_QUOTA", "16"))
        
        y, w = WeekUtils.get_week_key()
        with closing(db()) as conn:
            row = conn.execute(
                "SELECT id FROM weeks WHERE iso_year=? AND iso_week=?",
                (y, w)
            ).fetchone()
            if row:
                return row[0]
            conn.execute(
                "INSERT INTO weeks(iso_year, iso_week, quota) VALUES(?,?,?)",
                (y, w, default_quota)
            )
            conn.commit()
            return conn.execute(
                "SELECT id FROM weeks WHERE iso_year=? AND iso_week=?",
                (y, w)
            ).fetchone()[0]
    
    @staticmethod
    def get_current_week_needing_goalie() -> int | None:
        """Get current week ID if it needs a goalie (quota reached but not yet processed payment)"""
        week_id = WeekUtils.get_or_create_current_week()
        (iso_year, iso_week, quota, goalie_notified), signups = get_week_info(week_id)
        
        # Check if quota is reached and goalie was notified
        if len(signups) >= quota and goalie_notified:
            return week_id
        return None
