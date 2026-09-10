# SmartAttend — Face Recognition Attendance System

> Production-grade, real-time face recognition attendance for schools.
> A camera watches the entrance; enrolled students are detected, liveness-checked,
> and marked present automatically — with a live WebSocket dashboard.

## Features

- 👁️ **Real-time** face detection & recognition at 30+ FPS
- 🧵 **Multi-threaded pipeline** for smooth camera processing
- 👥 **Multi-face tracking** — ByteTrack-inspired centroid algorithm (20+ faces)
- ✅ **Multi-frame verification** prevents false positives before marking
- 🛡️ **Liveness detection** rejects photos and screen replays
- ♻️ **Duplicate prevention** with configurable cooldown (default 5 min)
- 📡 **WebSocket live updates** — attendance events pushed to the dashboard
- 🎨 **Premium light UI** with smooth animations
- 👤 **Role-based access** — Admin / Teacher / Viewer
- 📊 **Attendance reports** with CSV export
- 🧾 **Audit logging** for security events

## Tech Stack

| Layer      | Technology                                                   |
| ---------- | ------------------------------------------------------------ |
| Backend    | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0 (async)       |
| AI         | InsightFace (buffalo_sc), ONNX Runtime, OpenCV, NumPy        |
| Database   | SQLite / aiosqlite (dev), PostgreSQL (prod), Alembic         |
| Auth       | JWT (python-jose), passlib + bcrypt                          |
| Frontend   | React 18, TypeScript, Vite, Tailwind CSS 3.4, React Router 6, Recharts |
| Realtime   | WebSockets                                                   |
| Deploy     | Docker Compose (backend + frontend + Nginx), deploy scripts  |

## Performance

| Metric                   | Target                 |
| ------------------------ | ---------------------- |
| Camera FPS               | 30 FPS                 |
| Detection                | 15–30 ms per frame     |
| Recognition              | 10–25 ms per face (batch) |
| Total pipeline           | < 50 ms                |
| Max simultaneous faces   | 20+                    |

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/AayusX/smart-attend.git
cd smart-attend
cp .env.example .env
docker-compose up -d
```

### Local development

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Access

- Frontend: <http://localhost:3000>
- API docs: <http://localhost:8000/docs>

### First steps

1. Create an admin user:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"admin"}'
```

2. Log in at <http://localhost:3000> → add students → enroll faces → start camera.

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

## Project Structure

```
├── docker-compose.yml      # backend + frontend + nginx
├── .env.example            # documented environment variables
├── backend/
│   ├── app/
│   │   ├── api/            # auth, students, attendance, enrollment, reports
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # recognition, camera, tracker, enrollment
│   │   └── websocket/      # WebSocket connection manager
│   └── Dockerfile
├── frontend/
│   ├── src/pages/          # Dashboard, Students, Attendance, Enrollment, Reports, Login
│   └── Dockerfile
├── nginx/default.conf      # reverse proxy
└── scripts/
    ├── deploy.sh           # one-command deployment
    └── backup.sh           # DB + config backup (7-day rotation)
```

## Performance Optimizations

1. **Multi-threaded capture** — camera runs in its own thread
2. **Frame skipping** — detection runs every N frames
3. **Resolution scaling** — detect at 640px, not 1280px
4. **Batch recognition** — multiple faces processed at once
5. **Recognition caching** — verified faces aren't re-recognized
6. **ONNX optimizations** — graph optimization + thread pinning
7. **Smart frame selection** — recognize only when needed

## License

MIT