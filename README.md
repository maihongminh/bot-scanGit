#  GitHub Secret Scanner Bot

A comprehensive system for scanning GitHub repositories to detect exposed secrets, API keys, and other sensitive information using pattern matching and machine learning techniques.

##  Features

- ** Real-time Scanning**: Scan GitHub repositories for secrets in commits
- ** Multi-type Detection**: Detect AWS keys, API keys, SSH keys, database credentials, and more
- ** Dashboard**: Beautiful React-based web interface for managing scans and viewing results
- ** Async Processing**: Celery-based task queue for parallel scanning of multiple repositories
- ** Scheduled Scans**: Automatically scan trending repositories at regular intervals
- ** Statistics**: Comprehensive analytics on detected secrets by type, repository, and time
- ** False Positive Management**: Mark and manage false positives with custom reasons
- ** Docker Support**: Complete Docker and Docker Compose setup for easy deployment

##  Architecture

```
GitHub API (Trending + User repos)
    ↓
Collector Service
    ↓
Redis Queue (Celery)
    ↓
Worker Processes (Parallel scanning)
    ↓
Detection Engine (Regex patterns)
    ↓
PostgreSQL Database
    ↓
FastAPI Backend
    ↓
React Dashboard
```

##  Secret Types Detected

1. **AWS Keys** - AKIA format access keys
2. **Google API Keys** - AIza format
3. **OpenAI API Keys** - sk- format
4. **Claude API Keys** - claude- format
5. **GitHub Tokens** - ghp_, ghu_, ghs_ formats
6. **Slack Tokens** - xoxb-, xoxp- formats
7. **Database Credentials** - MongoDB, PostgreSQL, MySQL URIs
8. **SSH Private Keys** - RSA, DSA, EC, OpenSSH formats
9. **JWT Tokens** - Standard JWT format
10. **High-Entropy Strings** - Potential secrets

##  Quick Start

### Prerequisites

- Docker and Docker Compose
- GitHub Personal Access Token (optional but recommended)
- Python 3.10+ (for local development)
- Node.js 18+ (for frontend development)

### Docker Setup (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/bot-scanGit.git
cd bot-scanGit
```

2. **Create environment file**
```bash
cp backend/.env.example backend/.env
# Edit .env and add your GitHub token
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Initialize database**
```bash
docker-compose exec backend python init_db.py
```

5. **Access the application**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development Setup

#### Backend Setup

1. **Create Python virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup PostgreSQL**
```bash
psql -U postgres -c "CREATE DATABASE github_scanner;"
psql -U postgres -d github_scanner -f ../database/init.sql
```

4. **Setup Redis**
```bash
redis-server
```

5. **Create .env file**
```bash
cp .env.example .env
# Edit .env with your configuration
```

6. **Initialize database**
```bash
python init_db.py
```

7. **Start FastAPI server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Start Celery worker** (in a new terminal)
```bash
celery -A celery_app worker -l info
```

#### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Create environment file**
```bash
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env
```

3. **Start development server**
```bash
npm run dev
```

##  API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Repositories

#### List Repositories
```http
GET /repos/?skip=0&limit=50
```

#### Create Repository
```http
POST /repos/
Content-Type: application/json

{
  "name": "owner/repo",
  "url": "https://github.com/owner/repo",
  "description": "Optional description",
  "owner": "owner",
  "language": "python",
  "is_public": true
}
```

#### Get Repository Details
```http
GET /repos/{repository_id}
```

#### Get Repository Statistics
```http
GET /repos/{repository_id}/stats
```

### Detections

#### List Detections
```http
GET /detections/?repository_id=1&secret_type=aws_key&min_confidence=0.8
```

#### Get Detection Details
```http
GET /detections/{detection_id}
```

#### Mark as False Positive
```http
POST /detections/{detection_id}/false-positive
Content-Type: application/json

{
  "reason_code": "test_data",
  "reason_description": "This is test data in documentation",
  "marked_by": "user@example.com"
}
```

### Scanning

#### Start Repository Scan
```http
POST /scan/repository/{repository_id}
```

#### Scan Trending Repositories
```http
POST /scan/trending?language=python&limit=30
```

#### Get Scan Status
```http
GET /scan/repository/{repository_id}/status
```

#### Get Task Status
```http
GET /scan/task/{task_id}/status
```

### Statistics

#### Get Overview
```http
GET /stats/overview
```

#### Get Statistics by Secret Type
```http
GET /stats/by-type
```

#### Get Statistics by Repository
```http
GET /stats/by-repository
```

#### Get Timeline Statistics
```http
GET /stats/timeline?days=30
```

##  Dashboard Features

- **Repository Management**: Add, view, and manage repositories
- **Scan Control**: Start manual scans with progress tracking
- **Detection Viewer**: Browse all detected secrets with filtering
- **Statistics Dashboard**: Visualize detection trends and patterns
- **False Positive Management**: Mark and track false positives
- **Export Reports**: Download scan results as CSV/JSON

##  Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/github_scanner

# Redis
REDIS_URL=redis://localhost:6379/0

# GitHub
GITHUB_TOKEN=your_github_token
GITHUB_API_RATE_LIMIT=5000

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Scanner
MAX_WORKERS=5
SCAN_BATCH_SIZE=50
TRENDING_REPO_COUNT=30
MAX_COMMITS_PER_REPO=100
```

##  Testing

### Run Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Run Frontend Tests
```bash
cd frontend
npm test
```

##  Security Considerations

1. **Never commit `.env` files** with real credentials
2. **Use strong database passwords** in production
3. **Enable HTTPS** in production environments
4. **Rotate GitHub tokens** regularly
5. **Restrict API access** with authentication
6. **Monitor logs** for suspicious activity
7. **Validate all user inputs** server-side

##  Logging

Logs are stored in `backend/logs/app.log` and rotated when they exceed 10MB.

### Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical errors that may cause shutdown

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review the API documentation at `/docs`

##  Roadmap

- [ ] Web UI improvements and additional views
- [ ] Machine learning-based secret detection
- [ ] Slack/Email notifications for new secrets
- [ ] GitHub webhook integration for real-time scanning
- [ ] Multi-user support and team management
- [ ] Custom detection patterns
- [ ] Secret remediation automation
- [ ] Compliance reporting (SOC2, GDPR)

##  References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [React Documentation](https://react.dev/)

---

**Made with  by the Security Team**
