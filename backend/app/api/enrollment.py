from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.student import Student
from app.models.face_template import FaceTemplate
from app.schemas import EnrollmentStart
from app.api.auth import get_current_user
from app.models.user import User
from app.services.enrollment import EnrollmentService
from app.services.recognition import HighPerformanceRecognitionEngine

router = APIRouter(prefix="/api/enrollment", tags=["Enrollment"])

recognition_engine: HighPerformanceRecognitionEngine = None
enrollment_service: EnrollmentService = None


def init_enrollment_services(engine: HighPerformanceRecognitionEngine):
    global recognition_engine, enrollment_service
    recognition_engine = engine
    enrollment_service = EnrollmentService(engine)


@router.post("/start")
async def start_enrollment(data: EnrollmentStart, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    if not enrollment_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    student = await db.get(Student, data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    result = await db.execute(select(FaceTemplate).where(FaceTemplate.student_id == data.student_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Student already enrolled. Delete template first.")
    status = await enrollment_service.start_enrollment(data.student_id, data.num_samples)
    return {"message": "Enrollment started", "student_name": student.full_name, "samples_required": data.num_samples}


@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user)):
    if not enrollment_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return enrollment_service.get_status()


@router.post("/stop")
async def stop_enrollment(current_user: User = Depends(get_current_user)):
    if not enrollment_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    await enrollment_service.cancel_enrollment()
    return {"message": "Enrollment stopped"}


@router.delete("/student/{student_id}")
async def delete_template(student_id: int, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    if not enrollment_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    success = await enrollment_service.delete_student_template(db, student_id)
    if success:
        return {"message": "Template deleted"}
    raise HTTPException(status_code=500, detail="Failed to delete")


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(FaceTemplate))
    templates = result.scalars().all()
    response = []
    for t in templates:
        student = await db.get(Student, t.student_id)
        response.append({
            "id": t.id, "student_id": t.student_id,
            "student_name": student.full_name if student else "Unknown",
            "student_code": student.student_code if student else "Unknown",
            "model_version": t.model_version, "quality_score": t.quality_score,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    return response
