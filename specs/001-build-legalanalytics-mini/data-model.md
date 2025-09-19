# Data Model: LegalAnalytics Mini

## Entity Relationships

```
Employee (1) ----< TimeEntry (N)
Employee (N) ----< Department (1)
User (1) ----< Employee (1)
```

## Core Entities

### Employee
**Purpose**: Represents law firm staff members with their basic information and departmental assignment.

**Fields**:
- `id`: UUID primary key (auto-generated)
- `name`: String, required, max 100 characters
- `email`: String, required, unique, valid email format
- `department_id`: UUID, foreign key to Department
- `hire_date`: Date, required
- `created_at`: Timestamp, auto-generated
- `updated_at`: Timestamp, auto-updated

**Validation Rules**:
- Email must be unique across all employees
- Hire date cannot be in the future
- Name must contain at least first and last name (2 words minimum)
- Department must exist when employee is created

**SQLAlchemy vs JPA Comparison**:
```python
# SQLAlchemy (Python)
class Employee(Base):
    __tablename__ = 'employees'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)

# JPA (Java) equivalent
@Entity
@Table(name = "employees")
public class Employee {
    @Id
    @GeneratedValue
    private UUID id;

    @Column(length = 100, nullable = false)
    private String name;
}
```

### TimeEntry
**Purpose**: Represents billable work logged by employees with matter details and time spent.

**Fields**:
- `id`: UUID primary key (auto-generated)
- `employee_id`: UUID, foreign key to Employee, required
- `date`: Date, required
- `hours`: Decimal(5,2), required, min 0.01, max 24.00
- `description`: Text, required, max 500 characters
- `billable`: Boolean, required, default true
- `matter_code`: String, optional, max 20 characters
- `created_at`: Timestamp, auto-generated
- `updated_at`: Timestamp, auto-updated

**Validation Rules**:
- Date cannot be in the future
- Hours must be between 0.01 and 24.00
- Description must be at least 10 characters
- Employee must exist when time entry is created
- Matter code format: ABC-123 or ABC-123-DEF (optional)

**Business Rules**:
- Total hours per employee per day cannot exceed 24.00
- Deleted employees preserve historical time entries (soft delete pattern)

### Department
**Purpose**: Represents organizational divisions within the law firm.

**Fields**:
- `id`: UUID primary key (auto-generated)
- `name`: String, required, unique, max 50 characters
- `description`: Text, optional, max 200 characters
- `created_at`: Timestamp, auto-generated

**Validation Rules**:
- Name must be unique
- Name cannot be empty or whitespace only

**Predefined Data**:
- Corporate Law
- Litigation

### User
**Purpose**: Represents system authentication and authorization information.

**Fields**:
- `id`: UUID primary key (auto-generated)
- `username`: String, required, unique, max 50 characters
- `email`: String, required, unique, valid email format
- `hashed_password`: String, required (bcrypt hashed)
- `is_active`: Boolean, required, default true
- `role`: Enum(HR_ADMIN, LAWYER, PARTNER), required
- `employee_id`: UUID, optional foreign key to Employee
- `created_at`: Timestamp, auto-generated
- `last_login`: Timestamp, optional

**Validation Rules**:
- Username must be alphanumeric + underscore only
- Password must be at least 8 characters (before hashing)
- Email must be unique across all users
- Employee relationship is optional (for non-employee users)

**OAuth2 vs Spring Security Comparison**:
```python
# FastAPI OAuth2 (Python)
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    return {"access_token": token, "token_type": "bearer"}

# Spring Security (Java) equivalent
@PostMapping("/auth/login")
public ResponseEntity<JwtResponse> authenticateUser(@RequestBody LoginRequest loginRequest) {
    Authentication authentication = authenticationManager.authenticate(/*...*/);
    return ResponseEntity.ok(new JwtResponse(jwt));
}
```

## Database Schema

### Migration Strategy
- Use Alembic for database migrations (similar to Flyway/Liquibase)
- Version-controlled schema changes
- Rollback capabilities for each migration

### Indexing Strategy
```sql
-- Performance indexes for common queries
CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_timeentries_employee_date ON time_entries(employee_id, date);
CREATE INDEX idx_timeentries_date_billable ON time_entries(date, billable);
```

### Data Relationships

#### Employee ↔ TimeEntry (One-to-Many)
```python
# SQLAlchemy relationship definition
class Employee(Base):
    time_entries = relationship("TimeEntry", back_populates="employee")

class TimeEntry(Base):
    employee = relationship("Employee", back_populates="time_entries")
```

#### Department ↔ Employee (One-to-Many)
```python
class Department(Base):
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    department = relationship("Department", back_populates="employees")
```

## Data Access Patterns

### Repository Pattern Implementation
Following Spring Data JPA patterns but with SQLAlchemy:

```python
# Python SQLAlchemy pattern
class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_email(self, email: str) -> Optional[Employee]:
        return self.db.query(Employee).filter(Employee.email == email).first()

# Java JPA equivalent
@Repository
public interface EmployeeRepository extends JpaRepository<Employee, UUID> {
    Optional<Employee> findByEmail(String email);
}
```

### Query Optimization
- Use lazy loading for related entities by default
- Explicit eager loading for dashboard queries
- Pagination for large result sets
- Query result caching for department lookups

### Transaction Management
```python
# SQLAlchemy transaction pattern
@contextmanager
def db_transaction():
    try:
        db.begin()
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Spring @Transactional equivalent
@Transactional
public void updateEmployeeTimeEntries(UUID employeeId, List<TimeEntryDto> entries) {
    // Spring manages transaction boundaries automatically
}
```

## Elasticsearch Document Structure

### Employee Search Document
```json
{
  "_index": "employees",
  "_id": "uuid-here",
  "_source": {
    "name": "John Doe",
    "email": "john.doe@firm.com",
    "department": "Corporate Law",
    "hire_date": "2023-01-15",
    "status": "active"
  }
}
```

### Indexing Strategy
- Real-time indexing on employee create/update
- Batch reindexing for data consistency
- Search across name, email, and department fields
- Aggregations for dashboard department statistics

## File Storage Strategy

### Local Development
```python
# Local file storage with S3-like interface
class LocalFileStorage:
    def __init__(self, base_path="./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def upload_file(self, file_content: bytes, bucket: str, key: str):
        """Simulate S3 upload to local filesystem"""
        bucket_path = self.base_path / bucket
        bucket_path.mkdir(exist_ok=True)
        file_path = bucket_path / key
        file_path.write_bytes(file_content)
        return f"local://{bucket}/{key}"

    def get_file_url(self, bucket: str, key: str):
        """Generate local file URL for downloads"""
        return f"http://localhost:8000/files/{bucket}/{key}"

# AWS compatibility layer
def get_storage_client(use_local=True):
    if use_local:
        return LocalFileStorage()
    else:
        return boto3.client('s3')  # Real AWS when available
```

### File Processing Jobs
```python
# Local async processing with Celery + Redis
from celery import Celery

app = Celery('legalanalytics')
app.config_from_object({
    'broker_url': 'redis://localhost:6379/0',  # Local Redis instead of SQS
    'result_backend': 'redis://localhost:6379/0'
})

@app.task
def process_csv_file(file_path: str, file_type: str):
    """Process uploaded CSV file (same logic, different queue backend)"""
    # Same processing logic as AWS SQS version
    # Maintains learning value for async patterns
```

### Notification System
```python
# Local notifications (console + optional email)
class LocalNotificationService:
    def send_notification(self, message: str, topic: str):
        # Console output for development
        print(f"[{topic}] {message}")

        # Optional: Send actual email via SMTP for testing
        if settings.EMAIL_ENABLED:
            self.send_email(message, topic)

    def send_email(self, message: str, subject: str):
        # Local SMTP server (MailHog/MailCatcher for development)
        pass
```

## Performance Considerations

### Database Performance
- Connection pooling (SQLAlchemy engine configuration)
- Query result pagination for large datasets
- Database indexes on frequently queried columns
- Prepared statements to prevent SQL injection

### Memory Usage
- Lazy loading of relationships to minimize memory footprint
- Result set streaming for large CSV imports
- Connection pool size tuning based on concurrent users

### Scalability Patterns
- Read replicas for dashboard queries
- Database partitioning for time_entries by date
- Elasticsearch for search-heavy operations
- Async processing for file uploads (Redis/Celery locally, SQS in production)