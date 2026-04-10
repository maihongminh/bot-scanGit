#  GitHub Secret Scanner Bot - Setup Guide

This guide provides detailed instructions for setting up the GitHub Secret Scanner Bot in various environments.

## Table of Contents

1. [Docker Setup](#docker-setup)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Troubleshooting](#troubleshooting)

## Docker Setup

### Prerequisites
- Docker (version 20.10+)
- Docker Compose (version 1.29+)
- 4GB RAM minimum
- 10GB disk space

### Step-by-Step Instructions

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/bot-scanGit.git
cd bot-scanGit
```

#### 2. Configure Environment Variables
```bash
# Copy example env file
cp backend/.env.example backend/.env

# Edit the .env file with your settings
nano backend/.env
```

**Required environment variables:**
- `GITHUB_TOKEN`: Your GitHub Personal Access Token
- `DATABASE_URL`: PostgreSQL connection string (set by docker-compose by default)
- `REDIS_URL`: Redis connection URL (set by docker-compose by default)

#### 3. Start Services
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps
```

#### 4. Initialize Database
```bash
# Run database initialization
docker-compose exec backend python init_db.py

# Verify database is initialized
docker-compose exec postgres psql -U github_scanner -d github_scanner -c "\dt"
```

#### 5. Verify Installation
```bash
# Check backend health
curl http://localhost:8000/health

# Check API docs
curl http://localhost:8000/docs

# Check frontend
open http://localhost:3000
```

### Common Docker Commands

```bash
# View logs
docker-compose logs -f backend

# View specific service logs
docker-compose logs -f celery_worker

# Stop services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild services
docker-compose build --no-cache

# Execute command in container
docker-compose exec backend python manage.py shell
```

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Redis 7+
- Git

### Step 1: Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip postgresql postgresql-contrib redis-server nodejs npm
```

#### macOS (using Homebrew)
```bash
brew install python@3.10 postgresql redis node
```

#### Windows
Download and install:
- Python 3.10+ from python.org
- PostgreSQL from postgresql.org
- Redis from memurai.com or redis-windows
- Node.js from nodejs.org

### Step 2: Setup Backend

#### Create Python Virtual Environment
```bash
cd backend
python3 -m venv venv

# Activate virtual environment
# On Unix/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Setup Database

**Option 1: Using default postgres user**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE github_scanner;
CREATE USER github_scanner WITH PASSWORD 'your_password';
ALTER ROLE github_scanner SET client_encoding TO 'utf8';
ALTER ROLE github_scanner SET default_transaction_isolation TO 'read committed';
ALTER ROLE github_scanner SET default_transaction_deferrable TO on;
ALTER ROLE github_scanner SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE github_scanner TO github_scanner;

# Exit psql
\q
```

**Option 2: Using SQL script**
```bash
psql -U postgres -f ../database/init.sql
```

#### Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env
nano .env
```

**Set these values:**
```env
DATABASE_URL=postgresql://github_scanner:your_password@localhost:5432/github_scanner
REDIS_URL=redis://localhost:6379/0
GITHUB_TOKEN=your_github_token_here
DEBUG=True
```

#### Initialize Database
```bash
python init_db.py
```

#### Start FastAPI Server
```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using python module
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server should be available at `http://localhost:8000`

#### Start Celery Worker (New Terminal)
```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Start worker
celery -A celery_app worker -l info --concurrency=4
```

#### Start Celery Beat (Optional, New Terminal)
```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Start beat scheduler
celery -A celery_app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Step 3: Setup Frontend

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Configure Environment
```bash
# Create .env file
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env
```

#### Start Development Server
```bash
npm run dev
```

The frontend should be available at `http://localhost:5173` (or as shown in terminal)

## Production Deployment

### Prerequisites
- Docker and Docker Compose
- Domain name with SSL certificate
- PostgreSQL 13+ (managed service or self-hosted)
- Redis 7+ (managed service or self-hosted)

### Deployment Steps

#### 1. Prepare Production Environment
```bash
# Clone repository
git clone https://github.com/yourusername/bot-scanGit.git
cd bot-scanGit

# Create production env file
cp backend/.env.example backend/.env.production

# Generate secure secret keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 2. Configure for Production
```env
# backend/.env.production
DATABASE_URL=postgresql://github_scanner:strong_password@postgres-host:5432/github_scanner
REDIS_URL=redis://redis-host:6379/0
GITHUB_TOKEN=your_github_token
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
LOG_LEVEL=WARNING
FRONTEND_URL=https://yourdomain.com
```

#### 3. Update docker-compose.yml

```yaml
# Change port bindings and add reverse proxy
services:
  backend:
    environment:
      DEBUG: "False"
    ports:
      - "8000"  # No port binding, only internal
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
```

#### 4. Setup SSL/TLS
```bash
# Using Let's Encrypt with Certbot
sudo certbot certonly --standalone -d yourdomain.com

# Or copy your certificate files
cp /path/to/cert.pem ./ssl/cert.pem
cp /path/to/key.pem ./ssl/key.pem
```

#### 5. Start Production Services
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 6. Backup Strategy
```bash
# Regular database backups
docker-compose exec postgres pg_dump -U github_scanner github_scanner > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U github_scanner github_scanner > /backups/db_$DATE.sql
tar -czf /backups/db_$DATE.tar.gz /backups/db_$DATE.sql
```

## Troubleshooting

### Database Connection Issues

**Error: `psycopg2.OperationalError: could not connect to server`**

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection string in .env
DATABASE_URL=postgresql://user:password@localhost:5432/github_scanner
```

### Redis Connection Issues

**Error: `ConnectionError: Error 111 connecting to localhost:6379`**

```bash
# Check Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test Redis connection
redis-cli ping  # Should return PONG
```

### Celery Task Issues

**Error: `No celery app found`**

```bash
# Verify celery_app.py exists and imports correctly
python -c "from celery_app import celery_app; print(celery_app)"

# Check PYTHONPATH
export PYTHONPATH=$PWD

# Restart workers
docker-compose restart celery_worker
```

### GitHub API Rate Limiting

**Error: `API rate limit exceeded`**

```bash
# Check current rate limit
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit

# Options:
# 1. Use a higher-rate-limit token (GitHub Enterprise)
# 2. Increase GITHUB_API_RATE_LIMIT in .env
# 3. Implement caching strategies
```

### Memory Issues

**Error: `MemoryError` or `OOMKilled`**

```bash
# Increase Docker memory limit
# Edit docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

# Restart services
docker-compose up -d
```

### Frontend Not Loading

**Error: `Cannot GET /`**

```bash
# Check frontend service status
docker-compose ps frontend

# Check frontend logs
docker-compose logs frontend

# Verify API connection
curl http://localhost:8000/api/v1/repos/
```

### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check slow queries in PostgreSQL
# Enable slow query log
# postgresql.conf:
log_min_duration_statement = 1000  # 1 second

# Check Celery worker queue
celery -A celery_app inspect active

# Monitor Redis memory
redis-cli info memory
```

## Health Checks

### Backend Health Check
```bash
curl http://localhost:8000/health
# Response:
# {"status":"healthy","database":"connected"}
```

### Database Health Check
```bash
docker-compose exec postgres pg_isready -U github_scanner
# Response: accepting connections
```

### Redis Health Check
```bash
redis-cli ping
# Response: PONG
```

### Celery Worker Health Check
```bash
celery -A celery_app inspect ping
# Response: Worker is responsive
```

## Next Steps

After setup, proceed to:
1. [README.md](README.md) - Project overview and features
2. Add your first GitHub repository
3. Start a test scan
4. Explore the dashboard
5. Configure scanning schedules

For more help, check the API documentation at `/docs`
