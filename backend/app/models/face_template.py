from sqlalchemy import Column, Integer, String, DateTime, Float, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class FaceTemplate(Base):
    __tablename__ = "face_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    embedding = Column(LargeBinary, nullable=False)  # Encrypted numpy array
    model_version = Column(String(50), nullable=False)
    quality_score = Column(Float, nullable=True)
    sample_index = Column(Integer, default=0)  # Which enrollment sample
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    student = relationship("Student", back_populates="face_templates")
    
    def __repr__(self):
        return f"<FaceTemplate student_id={self.student_id}>"
