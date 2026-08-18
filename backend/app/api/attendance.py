from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from datetime import date, timedelta

from app.database import get_db
from app.models.attendance import AttendanceRecord, RecognitionEvent
from app.models.student import Student
from app.schemas import AttendanceResponse, AttendanceCorrection, AttendanceStats
from app.api.auth import get_current_user
from app.models.user import User
from app.services.attendance import AttendanceEngine

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

# Initialize attendance engine
attendance_engine = AttendanceEngine()


@router.get("/", response_model=List[AttendanceResponse])
async def list_attendance(
    student_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    class_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List attendance records with filters"""
    query = select(AttendanceRecord)
    
    if student_id:
        query = query.where(AttendanceRecord.student_id == student_id)
    if start_date:
        query = query.where(AttendanceRecord.session_date >= start_date)
    if end_date:
        query = query.where(AttendanceRecord.session_date <= end_date)
    if status:
        query = query.where(AttendanceRecord.status == status)
    
    query = query.order_by(AttendanceRecord.session_date.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Enrich with student info
    response = []
    for record in records:
        student = await db.get(Student, record.student_id)
        response.append({
            "id": record.id,
            "student_id": record.student_id,
            "student_name": student.full_name if student else None,
            "student_code": student.student_code if student else None,
            "session_date": record.session_date,
            "status": record.status,
            "check_in_time": record.check_in_time,
            "confidence": record.confidence,
            "camera_id": record.camera_id
        })
    
    return response


@router.get("/today")
async def get_today_attendance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get today's attendance summary"""
    today = date.today()
    
    # Get all active students
    result = await db.execute(
        select(Student).where(Student.status == "active")
    )
    all_students = result.scalars().all()
    total_students = len(all_students)
    
    # Get today's records
    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.session_date == today
        )
    )
    records = result.scalars().all()
    
    # Count by status
    present = sum(1 for r in records if r.status == "present")
    late = sum(1 for r in records if r.status == "late")
    absent = total_students - present - late
    
    # Get recent records with student info
    recent_records = []
    for record in sorted(records, key=lambda r: r.check_in_time or r.created_at, reverse=True)[:20]:
        student = await db.get(Student, record.student_id)
        recent_records.append({
            "student_name": student.full_name if student else "Unknown",
            "student_code": student.student_code if student else "Unknown",
            "status": record.status,
            "check_in_time": record.check_in_time.isoformat() if record.check_in_time else None,
            "confidence": record.confidence
        })
    
    return {
        "date": today.isoformat(),
        "total_students": total_students,
        "present": present,
        "late": late,
        "absent": max(0, absent),
        "attendance_percentage": round(((present + late) / total_students * 100) if total_students > 0 else 0, 1),
        "recent_records": recent_records
    }


@router.get("/stats", response_model=AttendanceStats)
async def get_stats(
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance statistics"""
    stats = await attendance_engine.get_attendance_stats(db, target_date)
    
    if "error" in stats:
        raise HTTPException(status_code=500, detail=stats["error"])
    
    return {
        "total_students": stats["total_students"],
        "present_today": stats["present"],
        "absent_today": stats["absent"],
        "late_today": stats["late"],
        "attendance_percentage": stats["attendance_percentage"]
    }


@router.put("/{record_id}/correct")
async def correct_attendance(
    record_id: int,
    correction: AttendanceCorrection,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually correct an attendance record"""
    result = await attendance_engine.correct_attendance(
        db=db,
        record_id=record_id,
        new_status=correction.status,
        corrected_by=current_user.username,
        reason=correction.reason
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/student/{student_id}")
async def get_student_attendance(
    student_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance history for a specific student"""
    # Verify student exists
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    history = await attendance_engine.get_student_attendance(db, student_id, days)
    
    # Calculate summary
    total_days = len(history)
    present_days = sum(1 for r in history if r["status"] in ["present", "late"])
    absent_days = total_days - present_days
    
    return {
        "student": {
            "id": student.id,
            "name": student.full_name,
            "code": student.student_code
        },
        "summary": {
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": absent_days,
            "attendance_percentage": round((present_days / total_days * 100) if total_days > 0 else 0, 1)
        },
        "history": history
    }


@router.get("/events")
async def list_recognition_events(
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List recent recognition events for debugging"""
    result = await db.execute(
        select(RecognitionEvent).order_by(RecognitionEvent.timestamp.desc()).limit(limit)
    )
    events = result.scalars().all()
    
    return [
        {
            "id": e.id,
            "student_id": e.student_id,
            "confidence": e.confidence,
            "liveness_passed": e.liveness_passed,
            "decision": e.decision,
            "timestamp": e.timestamp.isoformat()
        }
        for e in events
    ]
