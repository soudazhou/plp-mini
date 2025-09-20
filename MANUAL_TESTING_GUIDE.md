# LegalAnalytics Mini - Manual Testing Guide

## 🚀 Quick Start (5 minutes to working API)

### Prerequisites
- Python 3.11+ installed
- Docker and Docker Compose installed
- Git (to clone if needed)

### Step 1: Install Python Dependencies
```bash
cd backend
pip3 install -r requirements.txt
```

### Step 2: Start Infrastructure Services
```bash
cd ../infrastructure
docker-compose up -d postgres elasticsearch redis mailhog
```

Wait 30 seconds for services to start, then verify:
```bash
# Check if services are running
docker-compose ps

# Test database connection
docker exec -it legalanalytics-postgres psql -U dev -d legalanalytics -c "SELECT version();"
```

### Step 3: Setup Database
```bash
cd ../backend

# Copy environment configuration
cp .env.example .env

# Run database migrations
python3 -m alembic upgrade head

# Seed sample data
python3 scripts/seed_data.py
```

### Step 4: Start the API Server
```bash
# Start FastAPI server
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
```

## 🧪 Testing Endpoints

### 1. Health Check (No Auth Required)
```bash
# Test basic connectivity
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "environment": "development",
  "debug": true
}
```

### 2. Interactive API Documentation
Open your browser to: **http://localhost:8000/docs**

This gives you a complete interactive Swagger UI where you can:
- See all available endpoints
- Test each endpoint directly in the browser
- View request/response schemas
- Try different parameters

### 3. Employee API Testing (Manual curl commands)

#### Create a Department First
```bash
# We need a department to create employees
# Check existing departments
curl -X GET http://localhost:8000/api/v1/employees \
  -H "Content-Type: application/json"
```

#### Get Existing Departments (from seeded data)
Our seed script creates departments with known IDs. Let's use them:

#### Create a New Employee
```bash
# Create employee (replace DEPT_ID with actual department ID from seed data)
curl -X POST http://localhost:8000/api/v1/employees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane.smith@lawfirm.com",
    "department_id": "12345678-1234-5678-9abc-123456789012",
    "hire_date": "2023-01-15"
  }'
```

#### List All Employees
```bash
curl -X GET http://localhost:8000/api/v1/employees
```

#### Search Employees
```bash
curl -X GET "http://localhost:8000/api/v1/employees?search=Jane"
```

#### Get Specific Employee
```bash
# Replace EMPLOYEE_ID with actual ID from create response
curl -X GET http://localhost:8000/api/v1/employees/EMPLOYEE_ID
```

#### Update Employee
```bash
curl -X PUT http://localhost:8000/api/v1/employees/EMPLOYEE_ID \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane A. Smith"
  }'
```

## 🎯 Expected Test Results

### ✅ Successful Responses

**Employee Creation (201 Created):**
```json
{
  "id": "uuid-here",
  "name": "Jane Smith",
  "email": "jane.smith@lawfirm.com",
  "department": "Corporate Law",
  "hire_date": "2023-01-15",
  "created_at": "2023-12-01T10:30:00Z",
  "updated_at": "2023-12-01T10:30:00Z"
}
```

**Employee List (200 OK):**
```json
{
  "employees": [
    {
      "id": "uuid-here",
      "name": "Sarah Johnson",
      "email": "sarah.johnson@lawfirm.com",
      "department": "Corporate Law",
      "hire_date": "2020-03-15",
      "created_at": "2023-12-01T10:00:00Z",
      "updated_at": "2023-12-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 6,
    "pages": 1
  }
}
```

### ❌ Error Testing

**Invalid Email (400 Bad Request):**
```bash
curl -X POST http://localhost:8000/api/v1/employees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "invalid-email",
    "department_id": "12345678-1234-5678-9abc-123456789012",
    "hire_date": "2023-01-15"
  }'
```

Expected error response:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Duplicate Email (409 Conflict):**
```bash
# Try to create employee with existing email
curl -X POST http://localhost:8000/api/v1/employees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Another User",
    "email": "sarah.johnson@lawfirm.com",
    "department_id": "12345678-1234-5678-9abc-123456789012",
    "hire_date": "2023-01-15"
  }'
```

## 🎮 Interactive Testing with HTTPie (Optional)

If you prefer a more user-friendly tool than curl:

```bash
# Install HTTPie
pip install httpie

# Test with HTTPie (cleaner syntax)
http GET localhost:8000/health

http POST localhost:8000/api/v1/employees \
  name="John Doe" \
  email="john.doe@lawfirm.com" \
  department_id="12345678-1234-5678-9abc-123456789012" \
  hire_date="2023-01-15"
```

## 🕵️ Database Verification

Verify data is actually persisted:

```bash
# Connect to PostgreSQL to see the data
docker exec -it legalanalytics-postgres psql -U dev -d legalanalytics

# Inside PostgreSQL:
\dt                           # List tables
SELECT * FROM employees;      # See employee data
SELECT * FROM departments;    # See department data
\q                           # Quit
```

## 🔧 Troubleshooting

### Services Not Starting
```bash
# Check Docker services
docker-compose ps
docker-compose logs postgres
docker-compose logs elasticsearch

# Restart if needed
docker-compose down
docker-compose up -d
```

### Database Connection Issues
```bash
# Check if PostgreSQL is accessible
docker exec -it legalanalytics-postgres pg_isready -U dev

# Reset database if needed
docker-compose down -v  # Removes volumes
docker-compose up -d
```

### API Server Issues
```bash
# Check for port conflicts
lsof -i :8000

# Check logs for detailed errors
python3 -m uvicorn src.main:app --reload --log-level debug
```

### Python Dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 🎯 Performance Testing

Test API response times:
```bash
# Test response time
time curl -X GET http://localhost:8000/api/v1/employees

# Load testing (if Apache Bench installed)
ab -n 100 -c 10 http://localhost:8000/health
```

## 📱 Frontend Integration (Future)

Once you verify the API works, you can:
1. Start the Angular frontend: `ng serve --port 4200`
2. Access the UI at: `http://localhost:4200`
3. The frontend will call APIs at: `http://localhost:8000/api/v1/*`

## ✅ Success Criteria

You'll know everything is working when:
- ✅ Health endpoint returns 200 OK
- ✅ Swagger UI loads at /docs
- ✅ You can create employees via POST
- ✅ You can list employees via GET
- ✅ Search functionality works
- ✅ Error handling returns proper status codes
- ✅ Data persists in PostgreSQL database

This gives you a fully functional backend API that you can extend with additional features!