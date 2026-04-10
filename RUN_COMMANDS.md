# Commands to Run bot-scanGit Services

Quick reference for running each service individually.

---

## Prerequisites

Before running any service, ensure:
- Python 3.10+ installed
- Node.js 16+ installed
- PostgreSQL running
- Redis running (or start it below)

---

## 1. Redis (Message Broker & Cache)

### Start Redis Server on Port 6380 (bot-scanGit)
```bash
redis-server --port 6380
```

### Or run in background
```bash
redis-server --port 6380 &
```

### Check if Redis is running
```bash
redis-cli -p 6380 ping
# Output: PONG
```

### Connect to Redis CLI
```bash
redis-cli -p 6380
# Then you can use commands like:
# KEYS *
# GET key_name
# FLUSHALL (clear all data)
```

---

## 2. Backend (FastAPI)

### Navigate to backend
```bash
cd tool/bot-scanGit/backend
```

### Setup environment (first time only)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Create/Migrate database
```bash
# First time setup
python3 init_db.py

# Or if using Alembic for migrations
alembic upgrade head
```

### Set environment variables
```bash
# Copy example to .env
cp .env.example .env

# Edit .env and add GitHub token
nano .env  # or use your editor
# GITHUB_TOKEN=your_token_here
```

### Run Backend Server
```bash
# Make sure you're in backend directory
cd tool/bot-scanGit/backend

# Start FastAPI server with auto-reload
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or without auto-reload (production)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Access Backend
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 3. Celery Worker (Background Tasks)

### In a new terminal, navigate to backend
```bash
cd tool/bot-scanGit/backend

# Make sure virtual environment is activated
source venv/bin/activate
```

### Start Celery Worker
```bash
# Run Celery worker (processes scan tasks)
celery -A celery_app worker -l info

# Or with concurrency limit (recommended)
celery -A celery_app worker -l info --concurrency=2

# Or with specific queue
celery -A celery_app worker -l info -Q default,scanning
```

### Monitor Celery (optional - in another terminal)
```bash
# Install flower (Celery monitoring tool)
pip install flower

# Start Flower
celery -A app.celery_app flower --port=5555

# Access Flower UI: http://localhost:5555
```

---

## 4. Celery Beat (Scheduled Tasks)

### In a new terminal, navigate to backend
```bash
cd tool/bot-scanGit/backend

# Make sure virtual environment is activated
source venv/bin/activate
```

### Start Celery Beat (Scheduler)
```bash
# Run Celery Beat scheduler
celery -A celery_app beat -l info

# With specific schedule database
celery -A celery_app beat -l info --schedule=celerybeat-schedule
```

---

## 5. Frontend (React + Vite)

### Navigate to frontend
```bash
cd tool/bot-scanGit/frontend
```

### Setup environment (first time only)
```bash
# Install dependencies
npm install
# or
yarn install
```

### Create .env file
```bash
# Copy example
cp .env.example .env

# Edit .env
nano .env
# VITE_API_URL=http://localhost:8000/api/v1
```

### Run Development Server
```bash
# Make sure you're in frontend directory
cd tool/bot-scanGit/frontend

# Start Vite dev server
npm run dev
# or
yarn dev
```

### Access Frontend
- Frontend: http://localhost:5173

---

## Quick Reference - All Commands

### Terminal 1: Redis (port 6380)
```bash
redis-server --port 6380
```

### Terminal 2: PostgreSQL (if not already running)
```bash
# Depends on your setup, usually:
# docker run -d -p 5432:5432 postgres:14
# or check your PostgreSQL service
```

### Terminal 3: Backend
```bash
cd tool/bot-scanGit/backend
source venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 4: Celery Worker
```bash
cd tool/bot-scanGit/backend
source venv/bin/activate
celery -A celery_app worker -l info --concurrency=2
```

### Terminal 5: Celery Beat (optional)
```bash
cd tool/bot-scanGit/backend
source venv/bin/activate
celery -A celery_app beat -l info
```

### Terminal 6: Frontend
```bash
cd tool/bot-scanGit/frontend
npm run dev
```

---

## Verify Everything is Running

### Check Backend
```bash
curl http://localhost:8000/docs
# Should return Swagger UI
```

### Check Frontend
```bash
curl http://localhost:5173
# Should return HTML page
```

### Check Redis
```bash
redis-cli -p 6380 ping
# Output: PONG
```

### Check Celery
- Open http://localhost:5555 (if Flower running)
- Or check terminal for "worker online" messages

---

## Common Commands

### Kill a process on port
```bash
# Find process
lsof -i :8000
lsof -i :5173
lsof -i :5555
lsof -i :6379

# Kill by PID
kill -9 <PID>
```

### View logs
```bash
# Backend
tail -f backend/logs/app.log

# Celery
celery -A app.celery_app inspect active

# Celery stats
celery -A app.celery_app inspect stats
```

### Reset database
```bash
cd tool/bot-scanGit/backend
python3 -c "from app.models import Base; from app.database import engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

### Clear Redis
```bash
redis-cli FLUSHALL
```

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check if dependencies installed
pip list | grep fastapi

# Check database connection
python3 init_db.py
```

### Celery not processing tasks
```bash
# Check if Redis is running
redis-cli ping

# Check Celery logs
celery -A app.celery_app inspect active

# Restart Celery worker
```

### Frontend not loading
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database connection error
```bash
# Check PostgreSQL is running
# Verify connection string in .env
# Run init_db.py again
python3 init_db.py
```

---

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost/bot_scanGit
REDIS_URL=redis://localhost:6379/0
GITHUB_TOKEN=your_github_token
SECRET_KEY=your_secret_key
DEBUG=true
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Performance Tips

### Increase Celery concurrency
```bash
celery -A celery_app worker -l info --concurrency=8
```

### Use separate queues
```bash
# Worker 1: Scan tasks
celery -A celery_app worker -l info -Q scanning

# Worker 2: Other tasks
celery -A celery_app worker -l info -Q default
```

### Monitor with Flower
```bash
celery -A celery_app flower --port=5555
```

---

Last Updated: April 10, 2026
