from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    class_name = Column(String(20), nullable=True)
    section = Column(String(10), nullable=True)
    roll_number = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    status = Column(String(20), default="active")  # active, inactive, suspended
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    face_templates = relationship("FaceTemplate", back_populates="student", 
                                  cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="student",
                                     cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Student {self.student_code}: {self.full_name}>"
