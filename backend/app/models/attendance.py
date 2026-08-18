from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)  # present, late, absent, excused
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    confidence = Column(Float, nullable=True)
    camera_id = Column(String(50), nullable=True)
    verification_method = Column(String(50), default="face_recognition")
    is_manually_corrected = Column(Integer, default=0)  # 0=no, 1=yes
    corrected_by = Column(String(100), nullable=True)
    correction_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    student = relationship("Student", back_populates="attendance_records")
    
    def __repr__(self):
        return f"<Attendance student_id={self.student_id} date={self.session_date}>"


class RecognitionEvent(Base):
    """Log of all recognition attempts for debugging"""
    __tablename__ = "recognition_events"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=True)  # null if unknown
    track_id = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    liveness_score = Column(Float, nullable=True)
    liveness_passed = Column(Integer, default=0)  # 0=failed, 1=passed
    camera_id = Column(String(50), default="default")
    decision = Column(String(50), nullable=False)  # marked, duplicate, unknown, spoof_suspected
    frame_count = Column(Integer, nullable=True)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<RecognitionEvent decision={self.decision}>"
