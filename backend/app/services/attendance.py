from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, date, timezone, timedelta
import logging
import time

from app.models.student import Student
from app.models.attendance import AttendanceRecord, RecognitionEvent
from app.config import settings

logger = logging.getLogger(__name__)


class AttendanceEngine:
    def __init__(self):
        self.cooldown_tracker: Dict[int, float] = {}

    async def should_mark_attendance(self, db: AsyncSession, student_id: int,
                                    confidence: float, liveness_passed: bool) -> dict:
        if not liveness_passed:
            return {"should_mark": False, "status": "rejected", "reason": "liveness_failed"}

        if confidence < settings.RECOGNITION_THRESHOLD:
            return {"should_mark": False, "status": "rejected", "reason": "low_confidence"}

        current_time = time.time()
        if student_id in self.cooldown_tracker:
            time_since = current_time - self.cooldown_tracker[student_id]
            if time_since < settings.ATTENDANCE_COOLDOWN_SECONDS:
                return {"should_mark": False, "status": "cooldown", "reason": "wait"}

        today = date.today()
        existing = await self._get_existing(db, student_id, today)
        if existing:
            return {"should_mark": False, "status": "duplicate", "reason": "already_marked"}

        return {"should_mark": True, "status": "eligible", "reason": "ok"}

    async def mark_attendance(self, db: AsyncSession, student_id: int,
                             confidence: float, camera_id: str = "default") -> dict:
        try:
            today = date.today()
            now = datetime.now(timezone.utc)
            status = await self._determine_status(now)

            record = AttendanceRecord(
                student_id=student_id,
                session_date=today,
                status=status,
                check_in_time=now,
                confidence=confidence,
                camera_id=camera_id,
                verification_method="face_recognition"
            )
            db.add(record)
            await db.flush()

            self.cooldown_tracker[student_id] = time.time()

            event = RecognitionEvent(
                student_id=student_id,
                confidence=confidence,
                liveness_passed=1,
                camera_id=camera_id,
                decision="marked"
            )
            db.add(event)

            student = await db.get(Student, student_id)
            return {
                "id": record.id,
                "student_id": student_id,
                "student_name": student.full_name if student else None,
                "student_code": student.student_code if student else None,
                "status": status,
                "check_in_time": now.isoformat(),
                "confidence": confidence,
                "camera_id": camera_id
            }
        except Exception as e:
            logger.error(f"Attendance error: {e}")
            return {"error": str(e)}

    async def correct_attendance(self, db: AsyncSession, record_id: int,
                                new_status: str, corrected_by: str, reason: str) -> dict:
        try:
            record = await db.get(AttendanceRecord, record_id)
            if not record:
                return {"error": "Record not found"}
            old_status = record.status
            record.status = new_status
            record.is_manually_corrected = 1
            record.corrected_by = corrected_by
            record.correction_reason = reason

            event = RecognitionEvent(
                student_id=record.student_id,
                confidence=record.confidence,
                camera_id=record.camera_id,
                decision=f"corrected_{old_status}_to_{new_status}"
            )
            db.add(event)
            return {"id": record.id, "old_status": old_status, "new_status": new_status}
        except Exception as e:
            return {"error": str(e)}

    async def get_attendance_stats(self, db: AsyncSession, target_date: date = None) -> dict:
        if target_date is None:
            target_date = date.today()
        try:
            result = await db.execute(select(Student).where(Student.status == "active"))
            total = len(result.scalars().all())
            result = await db.execute(
                select(AttendanceRecord).where(AttendanceRecord.session_date == target_date)
            )
            records = result.scalars().all()
            present = sum(1 for r in records if r.status == "present")
            late = sum(1 for r in records if r.status == "late")
            absent = total - present - late
            pct = ((present + late) / total * 100) if total > 0 else 0
            return {
                "date": target_date.isoformat(),
                "total_students": total,
                "present": present,
                "late": late,
                "absent": max(0, absent),
                "attendance_percentage": round(pct, 1)
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_student_attendance(self, db: AsyncSession, student_id: int, days: int = 30) -> List[dict]:
        try:
            start_date = date.today() - timedelta(days=days)
            result = await db.execute(
                select(AttendanceRecord).where(
                    and_(AttendanceRecord.student_id == student_id,
                         AttendanceRecord.session_date >= start_date)
                ).order_by(AttendanceRecord.session_date.desc())
            )
            return [
                {"date": r.session_date.isoformat(), "status": r.status,
                 "check_in_time": r.check_in_time.isoformat() if r.check_in_time else None,
                 "confidence": r.confidence}
                for r in result.scalars().all()
            ]
        except Exception:
            return []

    async def _get_existing(self, db, student_id, target_date):
        result = await db.execute(
            select(AttendanceRecord).where(
                and_(AttendanceRecord.student_id == student_id,
                     AttendanceRecord.session_date == target_date)
            )
        )
        record = result.scalar_one_or_none()
        if record:
            return {"id": record.id, "status": record.status}
        return None

    async def _determine_status(self, check_in_time: datetime) -> str:
        hour = check_in_time.hour
        minute = check_in_time.minute
        if hour < 8 or (hour == 8 and minute <= 10):
            return "present"
        return "late"
