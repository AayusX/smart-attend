from app.api.auth import router as auth_router
from app.api.students import router as students_router
from app.api.attendance import router as attendance_router
from app.api.enrollment import router as enrollment_router
from app.api.reports import router as reports_router

__all__ = [
    "auth_router",
    "students_router", 
    "attendance_router",
    "enrollment_router",
    "reports_router"
]
