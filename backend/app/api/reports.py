from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional
from datetime import date, timedelta
import csv
import io

from app.database import get_db
from app.models.student import Student
from app.models.attendance import AttendanceRecord
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/daily")
async def daily_report(
    target_date: Optional[date] = None,
    class_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate daily attendance report"""
    if target_date is None:
        target_date = date.today()
    
    # Get students
    query = select(Student).where(Student.status == "active")
    if class_name:
        query = query.where(Student.class_name == class_name)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    # Get attendance records
    student_ids = [s.id for s in students]
    if student_ids:
        result = await db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id.in_(student_ids),
                    AttendanceRecord.session_date == target_date
                )
            )
        )
        records = {r.student_id: r for r in result.scalars().all()}
    else:
        records = {}
    
    # Build report
    report_students = []
    for student in students:
        record = records.get(student.id)
        report_students.append({
            "student_id": student.id,
            "student_code": student.student_code,
            "student_name": student.full_name,
            "class_name": student.class_name,
            "section": student.section,
            "status": record.status if record else "absent",
            "check_in_time": record.check_in_time.isoformat() if record and record.check_in_time else None,
            "confidence": record.confidence if record else None
        })
    
    # Summary
    total = len(students)
    present = sum(1 for s in report_students if s["status"] == "present")
    late = sum(1 for s in report_students if s["status"] == "late")
    absent = total - present - late
    
    return {
        "date": target_date.isoformat(),
        "class_name": class_name,
        "summary": {
            "total": total,
            "present": present,
            "late": late,
            "absent": absent,
            "attendance_percentage": round(((present + late) / total * 100) if total > 0 else 0, 1)
        },
        "students": report_students
    }


@router.get("/monthly")
async def monthly_report(
    year: int = Query(default=None),
    month: int = Query(default=None),
    class_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate monthly attendance report"""
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month
    
    # Get date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get students
    query = select(Student).where(Student.status == "active")
    if class_name:
        query = query.where(Student.class_name == class_name)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    # Get attendance records for the month
    student_ids = [s.id for s in students]
    if student_ids:
        result = await db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id.in_(student_ids),
                    AttendanceRecord.session_date >= start_date,
                    AttendanceRecord.session_date <= end_date
                )
            )
        )
        records = result.scalars().all()
    else:
        records = []
    
    # Group by student
    student_records = {}
    for record in records:
        if record.student_id not in student_records:
            student_records[record.student_id] = []
        student_records[record.student_id].append(record)
    
    # Calculate working days (excluding weekends for simplicity)
    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Monday to Friday
            working_days += 1
        current += timedelta(days=1)
    
    # Build report
    report_students = []
    for student in students:
        stu_records = student_records.get(student.id, [])
        present_days = sum(1 for r in stu_records if r.status in ["present", "late"])
        late_days = sum(1 for r in stu_records if r.status == "late")
        absent_days = working_days - present_days
        
        report_students.append({
            "student_id": student.id,
            "student_code": student.student_code,
            "student_name": student.full_name,
            "class_name": student.class_name,
            "total_working_days": working_days,
            "present_days": present_days,
            "late_days": late_days,
            "absent_days": max(0, absent_days),
            "attendance_percentage": round((present_days / working_days * 100) if working_days > 0 else 0, 1)
        })
    
    return {
        "year": year,
        "month": month,
        "class_name": class_name,
        "working_days": working_days,
        "students": report_students
    }


@router.get("/export/csv")
async def export_csv(
    start_date: date,
    end_date: date,
    class_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export attendance as CSV"""
    # Get students
    query = select(Student).where(Student.status == "active")
    if class_name:
        query = query.where(Student.class_name == class_name)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    # Get attendance records
    student_ids = [s.id for s in students]
    if student_ids:
        result = await db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id.in_(student_ids),
                    AttendanceRecord.session_date >= start_date,
                    AttendanceRecord.session_date <= end_date
                )
            )
        )
        records = result.scalars().all()
    else:
        records = []
    
    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Student Code", "Student Name", "Class", "Section",
        "Date", "Status", "Check In Time", "Confidence"
    ])
    
    # Data rows
    student_map = {s.id: s for s in students}
    for record in sorted(records, key=lambda r: (r.student_id, r.session_date)):
        student = student_map.get(record.student_id)
        if student:
            writer.writerow([
                student.student_code,
                student.full_name,
                student.class_name,
                student.section,
                record.session_date.isoformat(),
                record.status,
                record.check_in_time.isoformat() if record.check_in_time else "",
                f"{record.confidence:.2f}" if record.confidence else ""
            ])
    
    # Return as response
    from fastapi.responses import StreamingResponse
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=attendance_{start_date}_{end_date}.csv"
        }
    )


@router.get("/student/{student_id}")
async def student_report(
    student_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate report for a specific student"""
    # Verify student
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Default date range: last 30 days
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Get records
    result = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.session_date >= start_date,
                AttendanceRecord.session_date <= end_date
            )
        ).order_by(AttendanceRecord.session_date)
    )
    records = result.scalars().all()
    
    # Calculate working days
    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            working_days += 1
        current += timedelta(days=1)
    
    present_days = sum(1 for r in records if r.status in ["present", "late"])
    late_days = sum(1 for r in records if r.status == "late")
    absent_days = working_days - present_days
    
    return {
        "student": {
            "id": student.id,
            "code": student.student_code,
            "name": student.full_name,
            "class": student.class_name,
            "section": student.section
        },
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "working_days": working_days
        },
        "summary": {
            "present_days": present_days,
            "late_days": late_days,
            "absent_days": max(0, absent_days),
            "attendance_percentage": round((present_days / working_days * 100) if working_days > 0 else 0, 1)
        },
        "daily_records": [
            {
                "date": r.session_date.isoformat(),
                "status": r.status,
                "check_in_time": r.check_in_time.isoformat() if r.check_in_time else None,
                "confidence": r.confidence
            }
            for r in records
        ]
    }
