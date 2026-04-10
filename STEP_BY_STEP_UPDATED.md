#  Chạy Local - Hướng Dẫn Chi Tiết Từng Bước

**Dự án độc lập tại:** `/home/minhmh/tool/bot-scanGit`

##  Cấu Trúc Thư Mục

```
/home/minhmh/tool/bot-scanGit/
 backend/          (FastAPI application)
    app/          (Source code)
    venv/         (Virtual environment - sẽ to)
    requirements.txt
    celery_app.py
    init_db.py
    Dockerfile
    .env          (Sẽ tạo)
 frontend/         (React application)
    src/
    node_modules/ (Sẽ tạo)
    package.json
    Dockerfile
    .env          (Tùy chọn)
 database/         (SQL scripts)
    init.sql
 docker-compose.yml
 README.md
 SETUP.md
 RUN_LOCAL_UPDATED.md
 STEP_BY_STEP_UPDATED.md (File này)
```

---

##  BƯỚC 1: Kiểm Tra Yêu Cầu

### 1.1 Kiểm tra Python
```bash
python3 --version
# Kết quả: Python 3.10+ (bắt buộc)
```

### 1.2 Kiểm tra PostgreSQL
```bash
# macOS
brew list postgresql

# Linux
which psql

# Kiểm tra kết nối
psql -U postgres -c "SELECT 1"
```

### 1.3 Kiểm tra Redis
```bash
# macOS
brew list redis

# Linux
which redis-server

# Kiểm tra
redis-cli ping  # Kết quả: PONG
```

### 1.4 Kiểm tra Node.js
```bash
node --version  # Node 18+
npm --version   # npm 8+
```

---

##  BƯỚC 2: Chuẩn Bị Backend

### 2.1 Vào thư mục dự án
```bash
cd /home/minhmh/tool/bot-scanGit
pwd
# Kết quả: /home/minhmh/tool/bot-scanGit
```

### 2.2 Vào thư mục backend
```bash
cd /home/minhmh/tool/bot-scanGit/backend
pwd
# Kết quả: /home/minhmh/tool/bot-scanGit/backend
```

### 2.3 Tạo Virtual Environment
```bash
# Tạo venv
python3 -m venv venv

# Activate venv (chọn tùy OS)
# macOS/Linux:
source venv/bin/activate

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (CMD):
venv\Scripts\activate.bat

# Kiểm tra (sẽ thấy (venv) ở đầu)
# (venv) minhmh@machine backend $
```

### 2.4 Cài đặt Dependencies
```bash
# Vẫn trong /home/minhmh/tool/bot-scanGit/backend
# Cập nhật pip
pip install --upgrade pip

# Cài requirements
pip install -r requirements.txt

# Kiểm tra
pip list | grep fastapi
```

### 2.5 Tạo .env File
```bash
# Vẫn trong /home/minhmh/tool/bot-scanGit/backend
cp .env.example .env

# Xem nội dung
cat .env

# Chỉnh sửa nếu cần
nano .env
# Hoặc dùng editor yêu thích
```

**Nội dung .env (tối thiểu):**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/github_scanner
REDIS_URL=redis://localhost:6379/0
GITHUB_TOKEN=
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 2.6 Setup Database

#### 2.6.1 Khởi động PostgreSQL
```bash
# macOS (Homebrew)
brew services start postgresql

# Linux
sudo service postgresql start

# Windows - Mở Services.msc và start PostgreSQL

# Kiểm tra
psql -U postgres -c "SELECT 1"
```

#### 2.6.2 Tạo Database
```bash
# Đăng nhập PostgreSQL
psql -U postgres

# Chạy các lệnh sau:
CREATE DATABASE github_scanner;
CREATE USER github_scanner WITH PASSWORD 'password';
ALTER ROLE github_scanner SET client_encoding TO 'utf8';
ALTER ROLE github_scanner SET default_transaction_isolation TO 'read committed';
ALTER ROLE github_scanner SET default_transaction_deferrable TO on;
ALTER ROLE github_scanner SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE github_scanner TO github_scanner;
\q

# Hoặc chạy SQL script trực tiếp
psql -U postgres -d github_scanner -f /home/minhmh/tool/bot-scanGit/database/init.sql
```

#### 2.6.3 Kiểm tra Database
```bash
# Liệt kê databases
psql -U postgres -l

# Kết nối tới github_scanner
psql -U postgres -d github_scanner

# Kiểm tra tables
\dt

# Thoát
\q
```

### 2.7 Chạy Database Init Script
```bash
# Vẫn trong /home/minhmh/tool/bot-scanGit/backend
# venv đã activate

python init_db.py

# Kết quả mong đợi:
# Database initialized successfully!
```

---

##  BƯỚC 3: Chạy Backend (Terminal 1)

```bash
# Mở Terminal 1
# Vào thư mục backend
cd /home/minhmh/tool/bot-scanGit/backend

# Activate venv
source venv/bin/activate

# Chạy FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Kết quả mong đợi:
# Uvicorn running on http://0.0.0.0:8000
# Application startup complete
```

**Kiểm tra Backend chạy ok:**
```bash
# Mở Terminal mới
curl http://localhost:8000/health

# Kết quả:
# {"status":"healthy","database":"connected"}
```

**Xem API Docs:**
```bash
# Truy cập: http://localhost:8000/docs
# Sẽ thấy Swagger UI với tất cả endpoints
```

---

##  BƯỚC 4: Chạy Redis (Terminal 2)

```bash
# Mở Terminal 2 (giữ Terminal 1 chạy)

# Chạy Redis
redis-server

# Kết quả mong đợi:
# Ready to accept connections
```

**Kiểm tra Redis chạy ok:**
```bash
# Mở Terminal mới
redis-cli ping

# Kết quả:
# PONG
```

---

##  BƯỚC 5: Chạy Celery Worker (Terminal 3)

```bash
# Mở Terminal 3 (giữ Terminal 1, 2 chạy)

# Vào thư mục backend
cd /home/minhmh/tool/bot-scanGit/backend

# Activate venv
source venv/bin/activate

# Chạy Celery worker
celery -A celery_app worker -l info --concurrency=2

# Kết quả mong đợi:
# celery@... ready - ready to accept tasks
```

---

##  BƯỚC 6: Chạy Frontend (Terminal 4)

```bash
# Mở Terminal 4 (giữ Terminal 1, 2, 3 chạy)

# Vào thư mục frontend
cd /home/minhmh/tool/bot-scanGit/frontend

# Cài dependencies (lần đầu tiên)
npm install

# Chạy dev server
npm run dev

# Kết quả mong đợi:
# VITE v... ready in ... ms
#   Local:   http://localhost:5173/
```

---

##  BƯỚC 7: Kiểm Tra Toàn Bộ Hệ Thống

### 7.1 Kiểm tra Backend
```bash
# Health check
curl http://localhost:8000/health

# Xem API docs
# Truy cập: http://localhost:8000/docs
```

### 7.2 Kiểm tra Frontend
```bash
# Truy cập: http://localhost:5173
# Nên thấy: "GitHub Secret Scanner Bot" header
```

### 7.3 Kiểm tra Redis
```bash
redis-cli
> PING
PONG
> EXIT
```

### 7.4 Kiểm tra Celery
```bash
# Ở Terminal 3, kiểm tra:
# celery@... ready - ready to accept tasks
```

### 7.5 Kiểm tra PostgreSQL
```bash
psql -U postgres -d github_scanner -c "SELECT COUNT(*) FROM repositories;"
```

---

##  Test Ứng Dụng

### Test 1: Tạo Repository
```bash
curl -X POST http://localhost:8000/api/v1/repos/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test/repo",
    "url": "https://github.com/test/repo",
    "owner": "test",
    "language": "python",
    "is_public": true
  }'

# Kết quả: JSON với repo id=1
```

### Test 2: Lấy danh sách repositories
```bash
curl http://localhost:8000/api/v1/repos/

# Kết quả: JSON array với repositories
```

### Test 3: Khởi động scan
```bash
curl -X POST http://localhost:8000/api/v1/scan/repository/1

# Kết quả: Task ID và status "queued"
```

### Test 4: Kiểm tra task status
```bash
curl http://localhost:8000/api/v1/scan/task/TASK_ID/status

# Thay TASK_ID bằng ID từ Test 3
```

---

##  Tóm Tắt - 4 Terminal Cần Chạy

| Terminal | Thư Mục | Lệnh | URL |
|----------|---------|------|-----|
| **1** | `/home/minhmh/tool/bot-scanGit/backend` | `uvicorn app.main:app --reload` | http://localhost:8000 |
| **2** | Bất kỳ | `redis-server` | localhost:6379 |
| **3** | `/home/minhmh/tool/bot-scanGit/backend` | `celery -A celery_app worker -l info` | - |
| **4** | `/home/minhmh/tool/bot-scanGit/frontend` | `npm run dev` | http://localhost:5173 |

---

##  Troubleshooting

### Lỗi: "Address already in use"
```bash
# Tìm process đang dùng port
lsof -i :8000

# Kill process
kill -9 <PID>

# Hoặc đổi port trong .env
API_PORT=8001
```

### Lỗi: "Database connection refused"
```bash
# Kiểm tra PostgreSQL chạy
psql -U postgres -c "SELECT 1"

# Kiểm tra credentials trong .env
cat /home/minhmh/tool/bot-scanGit/backend/.env | grep DATABASE_URL
```

### Lỗi: "Redis connection error"
```bash
# Kiểm tra Redis chạy
redis-cli ping

# Khởi động Redis
redis-server
```

### Lỗi: "Module not found"
```bash
# Kiểm tra venv activate
which python
# Kết quả: /home/minhmh/tool/bot-scanGit/backend/venv/bin/python

# Reinstall
cd /home/minhmh/tool/bot-scanGit/backend
pip install -r requirements.txt
```

---

##  Cleanup (Khi xong)

```bash
# Tắt tất cả terminal (Ctrl+C)

# Deactivate venv (Terminal 1)
deactivate

# Dừng PostgreSQL
# macOS:
brew services stop postgresql

# Linux:
sudo service postgresql stop
```

---

##  Tóm Tắt Đường Dẫn

- **Dự án:** `/home/minhmh/tool/bot-scanGit`
- **Backend:** `/home/minhmh/tool/bot-scanGit/backend`
- **Frontend:** `/home/minhmh/tool/bot-scanGit/frontend`
- **Database script:** `/home/minhmh/tool/bot-scanGit/database/init.sql`
- **Cấu hình:** `/home/minhmh/tool/bot-scanGit/backend/.env`

---

**Bắt đầu từ Bước 1 và làm từng bước một!** 

**Tất cả nằm trong:** `/home/minhmh/tool/bot-scanGit` - Dự án độc lập
