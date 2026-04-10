#  Chạy Local - Hướng Dẫn Nhanh

**Dự án độc lập tại:** `/home/minhmh/tool/bot-scanGit`

## Yêu cầu
- Python 3.10+
- PostgreSQL
- Redis
- Node.js 18+

## Bước 1: Chuẩn bị Backend

### 1.1 Vào thư mục dự án
```bash
cd /home/minhmh/tool/bot-scanGit
pwd  # Kiểm tra: /home/minhmh/tool/bot-scanGit
```

### 1.2 Tạo Virtual Environment
```bash
cd /home/minhmh/tool/bot-scanGit/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.3 Cài dependencies
```bash
cd /home/minhmh/tool/bot-scanGit/backend
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.4 Tạo .env file
```bash
cd /home/minhmh/tool/bot-scanGit/backend
cp .env.example .env
# Chỉnh sửa .env với editor yêu thích
```

### 1.5 Setup Database
```bash
# Tạo database
createdb github_scanner
psql -d github_scanner < /home/minhmh/tool/bot-scanGit/database/init.sql

# Hoặc chạy init script
cd /home/minhmh/tool/bot-scanGit/backend
python init_db.py
```

### 1.6 Chạy Backend (Terminal 1)
```bash
cd /home/minhmh/tool/bot-scanGit/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Bước 2: Chạy Redis (Terminal 2)

```bash
redis-server
```

## Bước 3: Chạy Celery Worker (Terminal 3)

```bash
cd /home/minhmh/tool/bot-scanGit/backend
source venv/bin/activate
celery -A celery_app worker -l info --concurrency=2
```

## Bước 4: Chạy Frontend (Terminal 4)

```bash
cd /home/minhmh/tool/bot-scanGit/frontend
npm install
npm run dev
```

## Kiểm Tra

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173 (hoặc port khác)
- Health: http://localhost:8000/health

## Test API

```bash
# Tạo repository
curl -X POST http://localhost:8000/api/v1/repos/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test/repo",
    "url": "https://github.com/test/repo",
    "owner": "test",
    "language": "python"
  }'

# Lấy danh sách
curl http://localhost:8000/api/v1/repos/

# Khởi động scan
curl -X POST http://localhost:8000/api/v1/scan/repository/1
```

## Troubleshooting

### Port đang bận
```bash
lsof -i :8000
kill -9 <PID>
```

### Database error
```bash
psql -U postgres -d github_scanner -c "SELECT 1"
```

### Redis error
```bash
redis-cli ping  # Should return PONG
```

---

**Dự án:** GitHub Secret Scanner Bot  
**Thư mục:** `/home/minhmh/tool/bot-scanGit`  
**Độc lập:** Tất cả đều nằm trong thư mục này
