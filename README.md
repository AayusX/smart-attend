# SmartAttend - Face Recognition Attendance System

Production-grade real-time face recognition attendance system for schools.

## Features

- **30+ FPS** real-time face detection and recognition
- **Multi-threaded pipeline** for smooth camera processing
- **Multi-face tracking** with ByteTrack-inspired centroid algorithm
- **Multi-frame verification** prevents false positives
- **Liveness detection** rejects photos and videos
- **Duplicate prevention** with configurable cooldown
- **WebSocket live updates** for instant dashboard refresh
- **Premium light UI** with smooth animations
- **Role-based access** (Admin / Teacher / Viewer)
- **Attendance reports** with CSV export
- **Audit logging** for security events

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| AI | InsightFace (buffalo_sc), ONNX Runtime, OpenCV |
| Database | SQLite (dev), PostgreSQL (prod) |
| Frontend | React 18, TypeScript, Tailwind CSS |
| Real-time | WebSockets |
| Deploy | Docker Compose, Nginx |

## Performance

| Metric | Target |
|--------|--------|
| Camera FPS | 30 FPS |
| Detection | 15-30ms per frame |
| Recognition | 10-25ms per face (batch) |
| Total pipeline | < 50ms |
| Max simultaneous faces | 20+ |

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/aayusx/smart-attend.git
cd smart-attend
cp .env.example .env
docker-compose up -d
```

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Access

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## First Steps

1. Create admin:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"admin"}'
```

2. Login at http://localhost:3000
3. Add students
4. Enroll faces
5. Start camera

## Architecture

```
Camera (30 FPS)
    |
    v
[Capture Thread] --frame--> [Detection Thread] --faces--> [Recognition Thread]
    |                              |                              |
    v                              v                              v
 Latest Frame            Face Bboxes + Embeddings        Student IDs
                                                              |
                                                              v
                                                    [Attendance Engine]
                                                              |
                                                              v
                                                      [Database + WebSocket]
                                                              |
                                                              v
                                                       [React Dashboard]
```

## Performance Optimizations

1. **Multi-threaded capture** - Camera runs in separate thread
2. **Frame skipping** - Detection runs every N frames
3. **Resolution scaling** - Detect at 640px, not full 1280px
4. **Batch recognition** - Process multiple faces at once
5. **Recognition caching** - Don't re-recognize verified faces
6. **ONNX optimizations** - Graph optimization + thread pinning
7. **Smart frame selection** - Only recognize when needed

## License

MIT
