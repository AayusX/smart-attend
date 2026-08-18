from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


# Student Schemas
class StudentBase(BaseModel):
    student_code: str = Field(..., min_length=1, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    class_name: Optional[str] = None
    section: Optional[str] = None
    roll_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    roll_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class StudentResponse(StudentBase):
    id: int
    status: str
    created_at: datetime
    has_face_template: bool = False
    
    class Config:
        from_attributes = True


# Face Template Schemas
class FaceTemplateResponse(BaseModel):
    id: int
    student_id: int
    model_version: str
    quality_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Attendance Schemas
class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    student_code: Optional[str] = None
    session_date: date
    status: str
    check_in_time: Optional[datetime]
    confidence: Optional[float]
    camera_id: Optional[str]
    
    class Config:
        from_attributes = True


class AttendanceCorrection(BaseModel):
    status: str = Field(..., pattern="^(present|late|absent|excused)$")
    reason: str = Field(..., min_length=1, max_length=500)


class AttendanceStats(BaseModel):
    total_students: int
    present_today: int
    absent_today: int
    late_today: int
    attendance_percentage: float


# Recognition Event Schemas
class RecognitionEventResponse(BaseModel):
    id: int
    student_id: Optional[int]
    confidence: Optional[float]
    liveness_score: Optional[float]
    decision: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Enrollment Schemas
class EnrollmentStart(BaseModel):
    student_id: int
    num_samples: int = Field(default=5, ge=3, le=15)


class EnrollmentStatus(BaseModel):
    student_id: int
    student_name: str
    samples_captured: int
    samples_required: int
    is_complete: bool
    quality_scores: list[float]


# WebSocket Event Schemas
class LiveAttendanceEvent(BaseModel):
    event: str
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    student_code: Optional[str] = None
    status: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: datetime
    camera_id: str = "default"


class CameraStatusEvent(BaseModel):
    camera_id: str
    status: str  # online, offline, error
    fps: Optional[float] = None
    faces_detected: Optional[int] = None
    timestamp: datetime
