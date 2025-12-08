# Checkov Security Dashboard — Backend

Bản hướng dẫn này mô tả cách cài đặt, cấu hình và khởi động toàn bộ hệ thống (backend + frontend) trên máy mới, bao gồm PostgreSQL, virtualenv, biến môi trường, và các lệnh kiểm tra thường dùng.

## Yêu cầu

- Python 3.10+ (3.12 recommended)
- Node.js 18+
- PostgreSQL 12+
- Git
- (Tuỳ chọn) Docker

## Cấu trúc chính

- backend/ — mã backend (FastAPI)
- frontend/ — ứng dụng React (Vite)
- uploads/ — thư mục lưu file upload (create if missing)
- custom_policies/ — policy tuỳ chỉnh (nếu có)

---

## 1. Sao chép repository

```bash
cd /home/tunghv/Desktop
git clone <your-repo-url> Dashboard
cd Dashboard

```

## 2. Thiết lập backend (sử dụng venv tại `/home/tunghv/Desktop/Dashboard/backend/venv`)

```bash
./kill.sh
cd backend

# tạo hoặc dùng venv đã có (nếu chưa có)
python3 -m venv venv

# kích hoạt venv (luôn chạy các lệnh backend trong venv này)
source venv/bin/activate

# Cài đặt các gói phụ thuộc
pip install -r requirements.txt

```

## 3. Cấu hình biến môi trường

Tạo file `backend/.env` (ví dụ):

```
DATABASE_URL=postgresql://checkov_user:checkov_password@localhost/checkov_dashboard
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CUSTOM_POLICIES_DIR=/full/path/to/Dashboard/custom_policies
UPLOAD_DIR=/home/tunghv/Desktop/Dashboard/backend/uploads
CORS_ORIGINS=http://localhost:3000

```

Ghi chú:

- Đảm bảo `DATABASE_URL` trỏ tới PostgreSQL mong muốn.
- `UPLOAD_DIR` là đường dẫn server sẽ đọc/ghi file upload.

## 4. Tạo database & user (Postgres)

Cài postgresql

```jsx
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl status postgresql
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Ví dụ:

```sql
sudo -u postgres psql
DROP DATABASE checkov_dashboard;
CREATE DATABASE checkov_dashboard;
CREATE USER checkov_user WITH PASSWORD 'checkov_password';
GRANT ALL PRIVILEGES ON DATABASE checkov_dashboard TO checkov_user;
\q
sudo -u postgres psql -d checkov_dashboard -c "ALTER SCHEMA public OWNER TO checkov_user;"
sudo -u postgres psql -d checkov_dashboard -c "GRANT USAGE, CREATE ON SCHEMA public TO checkov_user;"
sudo -u postgres psql -d checkov_dashboard -c "GRANT ALL PRIVILEGES ON DATABASE checkov_dashboard TO checkov_user;"
sudo -u postgres psql -d checkov_dashboard -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO checkov_user;"
sudo -u postgres psql -d checkov_dashboard -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO checkov_user;"
```

## 5. Khởi tạo shema / import policies / Backend

Nếu repo có script khởi tạo:

```bash
source venv/bin/activate
python backend/scripts/init_db.py
python3 backend/scripts/import_checkov_policies.py
python3 backend/scripts/import_custom_policies.py
```


## 6. Tạo thư mục uploads và quyền

```bash
mkdir -p /home/tunghv/Desktop/Dashboard/backend/uploads
chmod -R 755 /home/tunghv/Desktop/Dashboard/backend/uploads

```

## 7. Thiết lập frontend

```bash
cd /home/tunghv/Desktop/Dashboard/frontend
npm install
```

## 9. Chay app

```json
./restart.sh
```