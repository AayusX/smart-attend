import numpy as np
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import time

from app.models.student import Student
from app.models.face_template import FaceTemplate
from app.services.recognition import HighPerformanceRecognitionEngine
from app.config import settings

logger = logging.getLogger(__name__)


class EnrollmentService:
    def __init__(self, recognition_engine: HighPerformanceRecognitionEngine):
        self.engine = recognition_engine
        self.active_enrollment: Optional[dict] = None
        self.required_samples = 5

    async def start_enrollment(self, student_id: int, num_samples: int = 5) -> dict:
        self.active_enrollment = {
            "student_id": student_id,
            "samples_required": num_samples,
            "samples_captured": 0,
            "embeddings": [],
            "quality_scores": [],
            "start_time": time.time()
        }
        return {
            "student_id": student_id,
            "samples_required": num_samples,
            "samples_captured": 0,
            "is_complete": False
        }

    async def capture_sample(self, frame: np.ndarray) -> dict:
        if not self.active_enrollment:
            return {"error": "No active enrollment"}

        detections = self.engine.detect_faces_fast(frame)

        if len(detections) == 0:
            return {"error": "No face detected", "samples_captured": self.active_enrollment["samples_captured"]}
        if len(detections) > 1:
            return {"error": "Multiple faces detected"}

        det = detections[0]
        if det.det_score < settings.DETECTION_THRESHOLD:
            return {"error": f"Face not clear (score: {det.det_score:.2f})"}

        embedding = det.embedding
        self.active_enrollment["embeddings"].append(embedding)
        self.active_enrollment["quality_scores"].append(det.det_score)
        self.active_enrollment["samples_captured"] += 1

        remaining = self.active_enrollment["samples_required"] - self.active_enrollment["samples_captured"]
        return {
            "samples_captured": self.active_enrollment["samples_captured"],
            "samples_remaining": remaining,
            "quality_score": det.det_score,
            "is_complete": self.active_enrollment["samples_captured"] >= self.active_enrollment["samples_required"]
        }

    async def complete_enrollment(self, db: AsyncSession) -> dict:
        if not self.active_enrollment:
            return {"error": "No active enrollment"}

        student_id = self.active_enrollment["student_id"]
        embeddings = self.active_enrollment["embeddings"]
        quality_scores = self.active_enrollment["quality_scores"]

        if len(embeddings) < 3:
            return {"error": "Need at least 3 samples"}

        try:
            avg_embedding = np.mean(embeddings, axis=0)
            avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
            avg_quality = np.mean(quality_scores)

            template = FaceTemplate(
                student_id=student_id,
                embedding=avg_embedding.tobytes(),
                model_version=settings.FACE_MODEL,
                quality_score=float(avg_quality),
                sample_index=0
            )
            db.add(template)
            await db.flush()

            self.engine.add_student_embedding(student_id, avg_embedding)

            result = {
                "student_id": student_id,
                "samples_used": len(embeddings),
                "quality_score": float(avg_quality),
                "status": "completed"
            }
            self.active_enrollment = None
            return result

        except Exception as e:
            logger.error(f"Enrollment error: {e}")
            return {"error": str(e)}

    async def cancel_enrollment(self):
        self.active_enrollment = None

    async def delete_student_template(self, db: AsyncSession, student_id: int) -> bool:
        try:
            result = await db.execute(
                select(FaceTemplate).where(FaceTemplate.student_id == student_id)
            )
            for template in result.scalars().all():
                await db.delete(template)
            self.engine.remove_student_embedding(student_id)
            return True
        except Exception as e:
            logger.error(f"Template deletion error: {e}")
            return False

    def get_status(self) -> dict:
        if not self.active_enrollment:
            return {"is_active": False}
        return {
            "is_active": True,
            "student_id": self.active_enrollment["student_id"],
            "samples_captured": self.active_enrollment["samples_captured"],
            "samples_required": self.active_enrollment["samples_required"],
            "is_complete": self.active_enrollment["samples_captured"] >= self.active_enrollment["samples_required"]
        }
