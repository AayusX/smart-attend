from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.database import get_db
from app.models.student import Student
from app.models.face_template import FaceTemplate
from app.schemas import StudentCreate, StudentUpdate, StudentResponse
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("/", response_model=List[StudentResponse])
async def list_students(
    status: Optional[str] = None,
    class_name: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all students with optional filters"""
    query = select(Student)
    
    if status:
        query = query.where(Student.status == status)
    if class_name:
        query = query.where(Student.class_name == class_name)
    if search:
        query = query.where(Student.full_name.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    students = result.scalars().all()
    
    # Add face template status
    response = []
    for student in students:
        # Check if student has face template
        template_result = await db.execute(
            select(FaceTemplate).where(FaceTemplate.student_id == student.id)
        )
        has_template = template_result.scalar_one_or_none() is not None
        
        student_dict = {
            "id": student.id,
            "student_code": student.student_code,
            "full_name": student.full_name,
            "class_name": student.class_name,
            "section": student.section,
            "roll_number": student.roll_number,
            "email": student.email,
            "phone": student.phone,
            "status": student.status,
            "created_at": student.created_at,
            "has_face_template": has_template
        }
        response.append(student_dict)
    
    return response


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student by ID"""
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check for face template
    template_result = await db.execute(
        select(FaceTemplate).where(FaceTemplate.student_id == student.id)
    )
    has_template = template_result.scalar_one_or_none() is not None
    
    return {
        "id": student.id,
        "student_code": student.student_code,
        "full_name": student.full_name,
        "class_name": student.class_name,
        "section": student.section,
        "roll_number": student.roll_number,
        "email": student.email,
        "phone": student.phone,
        "status": student.status,
        "created_at": student.created_at,
        "has_face_template": has_template
    }


@router.post("/", response_model=StudentResponse)
async def create_student(
    student_data: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new student"""
    # Check for duplicate student code
    result = await db.execute(
        select(Student).where(Student.student_code == student_data.student_code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Student code already exists")
    
    student = Student(**student_data.model_dump())
    db.add(student)
    await db.flush()
    
    return {
        "id": student.id,
        "student_code": student.student_code,
        "full_name": student.full_name,
        "class_name": student.class_name,
        "section": student.section,
        "roll_number": student.roll_number,
        "email": student.email,
        "phone": student.phone,
        "status": student.status,
        "created_at": student.created_at,
        "has_face_template": False
    }


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a student"""
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update fields
    update_data = student_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    
    await db.flush()
    
    # Check for face template
    template_result = await db.execute(
        select(FaceTemplate).where(FaceTemplate.student_id == student.id)
    )
    has_template = template_result.scalar_one_or_none() is not None
    
    return {
        "id": student.id,
        "student_code": student.student_code,
        "full_name": student.full_name,
        "class_name": student.class_name,
        "section": student.section,
        "roll_number": student.roll_number,
        "email": student.email,
        "phone": student.phone,
        "status": student.status,
        "created_at": student.created_at,
        "has_face_template": has_template
    }


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a student (soft delete - set status to inactive)"""
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Soft delete
    student.status = "inactive"
    await db.flush()
    
    return {"message": "Student deactivated", "student_id": student_id}


@router.get("/classes/list")
async def list_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all unique class names"""
    result = await db.execute(
        select(Student.class_name).where(Student.class_name.isnot(None)).distinct()
    )
    classes = [row[0] for row in result.all()]
    return {"classes": sorted(classes)}
