import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import numpy as np

from app.config import settings
from app.database import init_db, async_session
from app.api import (
    auth_router, students_router, attendance_router,
    enrollment_router, reports_router
)
from app.websocket import websocket_manager
from app.services.recognition import HighPerformanceRecognitionEngine
from app.services.camera import HighPerformanceCameraService
from app.services.tracker import CentroidTracker
from app.services.enrollment import EnrollmentService
from app.services.attendance import AttendanceEngine
from app.api.enrollment import init_enrollment_services
from sqlalchemy import select
from app.models.face_template import FaceTemplate

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

recognition_engine = HighPerformanceRecognitionEngine()
camera_service = HighPerformanceCameraService()
tracker = CentroidTracker()
attendance_engine = AttendanceEngine()

is_processing = False
frame_counter = 0


async def load_embeddings():
    async with async_session() as db:
        result = await db.execute(select(FaceTemplate))
        templates = result.scalars().all()
        count = 0
        for t in templates:
            embedding = np.frombuffer(t.embedding, dtype=np.float32)
            recognition_engine.add_student_embedding(t.student_id, embedding)
            count += 1
        logger.info(f"Loaded {count} student embeddings")


async def process_camera_frames():
    global is_processing, frame_counter
    is_processing = True
    logger.info("High-performance camera processing started")

    try:
        while is_processing:
            frame = await camera_service.get_frame()
            if frame is None:
                await asyncio.sleep(0.005)
                continue

            frame_counter += 1

            # Run detection every N frames for speed
            if frame_counter % recognition_engine.detection_interval != 0:
                await asyncio.sleep(0.005)
                continue

            # Detect faces
            detections = recognition_engine.detect_faces_fast(frame)

            if not detections:
                await asyncio.sleep(0.005)
                continue

            bboxes = [d.bbox for d in detections]
            embeddings = [d.embedding for d in detections]

            tracks = tracker.update(bboxes, embeddings)

            # Batch recognize tracks that need it
            to_recognize = []
            to_recognize_tracks = []
            for track in tracks:
                if track.needs_recognition and track.embedding is not None:
                    frames_since = frame_counter - track.last_recognition_frame
                    if frames_since >= recognition_engine.recognition_interval or track.frames_tracked <= 1:
                        to_recognize.append(track.embedding)
                        to_recognize_tracks.append(track)

            # Batch recognition
            if to_recognize:
                results = recognition_engine.recognize_face_batch(to_recognize)
                for (student_id, confidence), track in zip(results, to_recognize_tracks):
                    track.add_recognition(student_id, confidence)
                    track.student_id = student_id
                    track.confidence = confidence
                    track.last_recognition_frame = frame_counter

                    # Liveness check
                    pos_history = list(track.position_history)
                    is_live, live_score = recognition_engine.check_liveness_movement(pos_history)
                    track.is_live = is_live
                    track.liveness_score = live_score

                    # Check stable identity
                    stable_id = track.stable_identity
                    if stable_id is not None:
                        track.is_verified = True
                        track.stable_count += 1
                    else:
                        track.is_verified = False
                        track.stable_count = 0

                    # Mark attendance if eligible
                    if track.is_verified and track.stable_count >= settings.VERIFICATION_FRAMES:
                        async with async_session() as db:
                            decision = await attendance_engine.should_mark_attendance(
                                db, stable_id, confidence, is_live
                            )
                            if decision["should_mark"]:
                                result = await attendance_engine.mark_attendance(
                                    db, stable_id, confidence
                                )
                                if "error" not in result:
                                    await websocket_manager.broadcast("live-attendance", {
                                        "event": "attendance_marked",
                                        "student_id": result["student_id"],
                                        "student_name": result["student_name"],
                                        "student_code": result["student_code"],
                                        "status": result["status"],
                                        "confidence": round(confidence, 3)
                                    })
                                    track.stable_count = 0
                                    track.is_verified = False
                                await db.commit()

            # Broadcast status
            if frame_counter % 10 == 0:
                await websocket_manager.broadcast("camera-status", {
                    "camera_id": "default",
                    "status": "online",
                    "fps": camera_service.actual_fps,
                    "faces_detected": len(detections),
                    "tracks_active": len(tracks)
                })

            await asyncio.sleep(0.005)

    except Exception as e:
        logger.error(f"Processing error: {e}")
    finally:
        is_processing = False
        logger.info("Camera processing stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Smart Attendance System...")
    await init_db()
    success = await recognition_engine.initialize()
    if success:
        await load_embeddings()
    init_enrollment_services(recognition_engine)
    logger.info("System ready")
    yield
    logger.info("Shutting down...")
    global is_processing
    is_processing = False
    if camera_service.is_running:
        await camera_service.stop()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(students_router)
app.include_router(attendance_router)
app.include_router(enrollment_router)
app.include_router(reports_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "recognition_engine": recognition_engine.is_initialized,
        "camera_active": camera_service.is_running,
        "processing": is_processing,
        "performance": recognition_engine.get_performance_stats()
    }


@app.post("/api/camera/start")
async def start_camera():
    global is_processing
    if is_processing:
        return {"message": "Already running"}
    success = await camera_service.start()
    if not success:
        return {"error": "Failed to start camera"}
    asyncio.create_task(process_camera_frames())
    return {"message": "Camera started"}


@app.post("/api/camera/stop")
async def stop_camera():
    global is_processing
    is_processing = False
    if camera_service.is_running:
        await camera_service.stop()
    return {"message": "Camera stopped"}


@app.get("/api/camera/status")
async def camera_status():
    return {
        "camera": camera_service.get_status(),
        "processing": is_processing,
        "recognition": recognition_engine.get_performance_stats()
    }


@app.post("/api/recognition/load-embeddings")
async def reload_embeddings():
    await load_embeddings()
    return {"message": "Reloaded", "count": len(recognition_engine.known_embeddings)}


@app.websocket("/ws/live-attendance")
async def ws_live(websocket: WebSocket):
    await websocket_manager.connect(websocket, "live-attendance")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, "live-attendance")


@app.websocket("/ws/camera-status")
async def ws_camera(websocket: WebSocket):
    await websocket_manager.connect(websocket, "camera-status")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, "camera-status")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
