# LegalAnalytics Mini - Quickstart Guide

## Overview
This quickstart guide demonstrates the core functionality of LegalAnalytics Mini through a series of integration tests that validate each user story from the specification.

## Prerequisites
- Python 3.11+ and Node.js 18+ installed
- Docker and Docker Compose installed
- No AWS account required! (We'll use local alternatives)

## Quick Setup Commands

### 1. Environment Setup
```bash
# Clone and setup
git clone <repository-url>
cd legalanalytics-mini

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Infrastructure setup (local AWS alternatives)
cd ../infrastructure
docker-compose up -d postgres elasticsearch redis mailhog
```

### Local AWS Services Setup
```yaml
# docker-compose.yml includes local alternatives
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: legalanalytics
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
    ports:
      - "5432:5432"

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Optional: Email testing (replaces SNS)
  mailhog:
    image: mailhog/mailhog
    ports:
      - "8025:8025"  # Web UI
      - "1025:1025"  # SMTP

  # Optional: S3-compatible storage
  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    command: server /data --console-address ":9001"
```

### 2. Database Initialization
```bash
# From backend directory
alembic upgrade head
python scripts/seed_data.py  # Creates sample departments and test user
```

### 3. Configuration
```bash
# Create local environment file
cd backend
cp .env.example .env

# Edit .env for local development
cat > .env << EOF
# Database
DATABASE_URL=postgresql://dev:dev123@localhost:5432/legalanalytics

# Redis (replaces SQS)
REDIS_URL=redis://localhost:6379/0

# File Storage (local instead of S3)
USE_LOCAL_STORAGE=true
LOCAL_STORAGE_PATH=./storage

# Email (optional, for notifications)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Development settings
DEBUG=true
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
EOF
```

### 4. Start Services
```bash
# Terminal 1: Backend API
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
ng serve --port 4200

# Terminal 3: Background job processor (Redis instead of SQS)
cd backend
celery -A app.worker worker --loglevel=info

# Terminal 4: Optional - Monitor jobs
cd backend
celery -A app.worker flower  # Job monitoring UI at http://localhost:5555
```

## Integration Test Scenarios

### Test 1: Employee Management (FR-001 to FR-005)
**User Story**: HR admin manages employee records

#### Steps:
1. **Login as HR Admin**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "hr_admin", "password": "test123"}'
   ```
   **Expected**: JWT token returned

2. **Create New Employee**
   ```bash
   curl -X POST http://localhost:8000/api/v1/employees \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "John Doe",
       "email": "john.doe@lawfirm.com",
       "department_id": "corp-law-uuid",
       "hire_date": "2023-01-15"
     }'
   ```
   **Expected**: Employee created with 201 status, returns employee object with ID

3. **List All Employees**
   ```bash
   curl -X GET http://localhost:8000/api/v1/employees \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Array with John Doe included, pagination metadata

4. **Search Employee by Name**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/employees?search=John" \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Filtered results containing John Doe

5. **Update Employee Information**
   ```bash
   curl -X PUT http://localhost:8000/api/v1/employees/$EMPLOYEE_ID \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "John A. Doe"}'
   ```
   **Expected**: Updated employee object returned

6. **Delete Employee**
   ```bash
   curl -X DELETE http://localhost:8000/api/v1/employees/$EMPLOYEE_ID \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: 204 No Content status

**Validation Points**:
- Employee appears in list immediately after creation
- Search returns partial matches
- Email uniqueness is enforced
- Deleted employees don't appear in regular lists

### Test 2: Time Tracking (FR-006 to FR-008)
**User Story**: Lawyer logs billable hours and views totals

#### Steps:
1. **Login as Lawyer**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "lawyer_user", "password": "test123"}'
   ```

2. **Log Time Entry**
   ```bash
   curl -X POST http://localhost:8000/api/v1/time-entries \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "employee_id": "$EMPLOYEE_ID",
       "date": "2023-01-15",
       "hours": 7.5,
       "description": "Contract review for ABC Corp merger",
       "billable": true,
       "matter_code": "ABC-123"
     }'
   ```
   **Expected**: Time entry created, returns entry with ID

3. **View Time Entries**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/time-entries?employee_id=$EMPLOYEE_ID" \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: List includes the logged entry in chronological order

4. **Get Monthly Summary**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/time-entries/summary?employee_id=$EMPLOYEE_ID&start_date=2023-01-01&end_date=2023-01-31" \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Summary shows 7.5 total hours, 7.5 billable hours for January

**Validation Points**:
- Time entry appears in list immediately
- Monthly totals are calculated correctly
- Billable vs non-billable hours are tracked separately
- Cannot log negative hours or future dates

### Test 3: Dashboard Analytics (FR-009 to FR-010)
**User Story**: Partner views firm-wide dashboard metrics

#### Steps:
1. **Login as Partner**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "partner_user", "password": "test123"}'
   ```

2. **Get Dashboard Overview**
   ```bash
   curl -X GET http://localhost:8000/api/v1/dashboard/overview \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Shows total employees, total billable hours this month, average utilization rate

3. **Get Department Hours Breakdown**
   ```bash
   curl -X GET http://localhost:8000/api/v1/dashboard/department-hours \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Array of departments with hours worked, suitable for bar chart

4. **Get Utilization Rates**
   ```bash
   curl -X GET http://localhost:8000/api/v1/dashboard/utilization \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Per-employee utilization rates with firm average

**Validation Points**:
- Dashboard metrics update immediately after new time entries
- Department breakdown sums to total hours
- Utilization rates are calculated as billable/total hours
- Charts display meaningful data even with minimal sample data

### Test 4: CSV Data Upload (FR-011 to FR-013)
**User Story**: HR admin uploads employee and time data from CSV files

#### Steps:
1. **Download Employee Template**
   ```bash
   curl -X GET http://localhost:8000/api/v1/upload/templates/employees \
     -H "Authorization: Bearer $TOKEN" \
     -o employee_template.csv
   ```
   **Expected**: CSV file with proper headers and sample data

2. **Upload Employee CSV**
   ```bash
   curl -X POST http://localhost:8000/api/v1/upload/employees \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@test_employees.csv" \
     -F "overwrite_existing=false"
   ```
   **Expected**: Job ID returned, status shows "pending" or "processing"

3. **Check Upload Status**
   ```bash
   curl -X GET http://localhost:8000/api/v1/upload/status/$JOB_ID \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Progress updates, eventually shows "completed" with processed row counts

4. **Upload Time Entries CSV**
   ```bash
   curl -X POST http://localhost:8000/api/v1/upload/time-entries \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@test_timeentries.csv"
   ```
   **Expected**: Similar async processing with job tracking

5. **View Upload History**
   ```bash
   curl -X GET http://localhost:8000/api/v1/upload/history \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: List of previous uploads with status and summary

**Validation Points**:
- CSV processing happens asynchronously
- Progress is trackable via job status API
- Malformed CSV rows are reported as errors
- Successful uploads immediately appear in employee/time entry lists
- SNS notifications are sent upon completion

### Test 5: Employee Search (FR-005 with Elasticsearch)
**User Story**: User searches employees by name or department

#### Steps:
1. **Advanced Employee Search**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/employees/search?q=corporate+law" \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Full-text search results including employees in Corporate Law department

2. **Partial Name Search**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/employees/search?q=john" \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Employees with "john" in their name (case-insensitive)

3. **Department Filter with Search**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/employees/search?q=law&department=litigation" \
     -H "Authorization: Bearer $TOKEN"
   ```
   **Expected**: Combined search and filter results

**Validation Points**:
- Search indexes are updated when employees are created/updated
- Partial matching works for names and departments
- Search is case-insensitive
- Results are ranked by relevance

## Frontend Integration Tests

### Web Application Flow Tests
Access the frontend at `http://localhost:4200` and test:

1. **Employee Management Interface**
   - Navigate to Employees page
   - Add new employee using form
   - Edit existing employee
   - Search employees using search box
   - Verify real-time updates

2. **Time Tracking Interface**
   - Navigate to Time Tracking page
   - Log new time entry
   - View time entries list
   - Check monthly summary calculation

3. **Dashboard Interface**
   - Navigate to Dashboard page
   - Verify metrics display correctly
   - Check that charts render department hours
   - Confirm utilization rates are shown

4. **File Upload Interface**
   - Navigate to Data Upload page
   - Download CSV templates
   - Upload sample CSV files
   - Monitor upload progress
   - View upload history

## Performance Validation

### Response Time Tests
```bash
# Test API response times
for i in {1..10}; do
  curl -w "%{time_total}\n" -o /dev/null -s \
    -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/employees
done
```
**Expected**: Average response time < 200ms

### Concurrent User Simulation
```bash
# Install Apache Bench
# Test with 10 concurrent users, 100 requests
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
   http://localhost:8000/api/v1/dashboard/overview
```
**Expected**: No errors, consistent response times

## Data Validation

### Sample Data Verification
After running all tests, verify:

1. **Employee Records**
   - At least 10 employees exist
   - All employees have valid departments
   - Email addresses are unique

2. **Time Entry Records**
   - At least 50 time entries exist
   - Hours are within valid range (0.01-24.00)
   - All entries link to valid employees

3. **Dashboard Calculations**
   - Total hours = sum of all time entries
   - Utilization rates = billable hours / total hours
   - Department totals = sum of employee hours by department

## Local AWS Alternative Validation

### Local File Storage
```bash
# Check local file storage
ls -la backend/storage/uploads/
```
**Expected**: Uploaded CSV files are stored with proper naming

### Redis Job Processing
```bash
# Check Redis queue status
redis-cli -h localhost -p 6379 info keyspace
redis-cli -h localhost -p 6379 llen celery

# Monitor Celery worker logs
tail -f backend/logs/celery.log
```
**Expected**: Jobs are processed and Redis queues are emptied

### Local Notifications
Check console output and MailHog UI:
```bash
# View notification logs
tail -f backend/logs/notifications.log

# Check MailHog web interface
open http://localhost:8025
```
**Expected**: Notifications appear in console and/or MailHog inbox

### Optional: MinIO S3 Alternative
If using MinIO instead of local file storage:
```bash
# Access MinIO console
open http://localhost:9001

# Check bucket contents via API
curl -X GET http://localhost:9000/uploads/
```

## Troubleshooting

### Common Issues
1. **Database Connection**: Ensure PostgreSQL is running on port 5432
   ```bash
   docker ps | grep postgres
   docker logs legalanalytics-postgres
   ```

2. **Elasticsearch**: Check that Elasticsearch is accessible on port 9200
   ```bash
   curl http://localhost:9200/_cluster/health
   docker logs legalanalytics-elasticsearch
   ```

3. **Redis Connection**: Ensure Redis is running for job processing
   ```bash
   redis-cli ping  # Should return PONG
   docker logs legalanalytics-redis
   ```

4. **CORS Errors**: Verify frontend is served from http://localhost:4200

5. **JWT Tokens**: Tokens expire after 24 hours, re-login if needed

6. **File Uploads**: Check local storage permissions
   ```bash
   ls -la backend/storage/
   chmod 755 backend/storage/
   ```

7. **Local vs AWS Mode**: Verify environment variables
   ```bash
   echo $USE_LOCAL_STORAGE  # Should be "true"
   ```

### Logs to Check
```bash
# Backend logs
tail -f backend/logs/app.log

# Worker logs (Celery instead of SQS)
tail -f backend/logs/celery.log

# Notification logs
tail -f backend/logs/notifications.log

# Frontend console
# Open browser dev tools and check console for errors

# Docker services
docker-compose logs postgres
docker-compose logs elasticsearch
docker-compose logs redis
```

### Service Health Checks
```bash
# Check all local services
curl http://localhost:8000/health          # Backend API
curl http://localhost:9200/_cluster/health # Elasticsearch
redis-cli ping                             # Redis
curl http://localhost:8025/api/v1/messages # MailHog (if used)
```

## Success Criteria
All integration tests pass when:
- ✅ Employees can be created, read, updated, deleted
- ✅ Time entries are logged and calculated correctly
- ✅ Dashboard shows real-time metrics
- ✅ CSV uploads process successfully with progress tracking
- ✅ Search returns accurate results
- ✅ Frontend interfaces work without errors
- ✅ API response times are under 200ms
- ✅ Local AWS alternatives work properly (Redis jobs, file storage, notifications)

## Learning Benefits of Local Setup
This local development approach provides several educational advantages:

1. **Zero Cost Learning**: No AWS charges while exploring cloud patterns
2. **Faster Iteration**: Local services start/stop quickly for development
3. **AWS Pattern Preservation**: Code structure remains AWS-compatible for easy migration
4. **Service Understanding**: Learn how each AWS service works by using local equivalents
5. **Production Readiness**: Environment variables easily switch between local and cloud

## Migration to Real AWS
When ready to deploy to AWS, simply change environment variables:
```bash
# Switch to AWS mode
USE_LOCAL_STORAGE=false
AWS_S3_BUCKET=your-bucket-name
AWS_SQS_URL=your-queue-url
AWS_SNS_TOPIC=your-topic-arn
```

The codebase maintains compatibility with both local and AWS backends, demonstrating a professional approach to environment-agnostic development.

This completes the validation that LegalAnalytics Mini meets all functional requirements from the specification while remaining accessible without AWS prerequisites.