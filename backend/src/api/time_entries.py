"""
Time Entry API Endpoints
T063-T068 - Time entry CRUD operations

FastAPI routes for time entry management with comprehensive validation,
filtering, and business logic. Follows REST conventions.

Spring Boot equivalent:
@RestController
@RequestMapping("/api/v1/time-entries")
public class TimeEntryController {
    @PostMapping
    public ResponseEntity<TimeEntryResponse> createTimeEntry(@RequestBody CreateTimeEntryRequest request) { ... }

    @GetMapping
    public ResponseEntity<Page<TimeEntryResponse>> getTimeEntries(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size,
        TimeEntryFilter filter
    ) { ... }
}
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from database import get_db
from services.time_entry_service import TimeEntryService
from repositories.time_entry_repository import TimeEntryRepository
from repositories.employee_repository import EmployeeRepository


# Router instance
router = APIRouter(prefix="/time-entries", tags=["time-entries"])


# Pydantic Models for Request/Response

class TimeEntryCreate(BaseModel):
    """
    Time entry creation request model

    Spring Boot equivalent:
    public class CreateTimeEntryRequest {
        @NotNull
        private UUID employeeId;

        @NotNull
        @PastOrPresent
        private LocalDate date;

        @DecimalMin("0.1")
        @DecimalMax("24.0")
        private BigDecimal hours;

        @NotBlank
        @Size(min = 10, max = 1000)
        private String description;

        private Boolean billable = false;
    }
    """
    employee_id: UUID = Field(..., description="Employee who worked the hours")
    date: date_type = Field(..., description="Date of work")
    hours: float = Field(..., ge=0.1, le=24.0, description="Hours worked (decimal allowed)")
    description: str = Field(..., min_length=10, max_length=1000, description="Work description")
    billable: bool = Field(default=False, description="Whether time is billable")

    @validator('date')
    def validate_date_not_future(cls, v):
        if v > date_type.today():
            raise ValueError('Date cannot be in the future')
        return v

    @validator('description')
    def validate_billable_description(cls, v, values):
        if values.get('billable', False) and len(v.strip()) < 20:
            raise ValueError('Billable time requires detailed description (minimum 20 characters)')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "12345678-1234-5678-9abc-123456789012",
                "date": "2023-12-01",
                "hours": 8.0,
                "description": "Worked on client project specifications and requirements gathering",
                "billable": True
            }
        }


class TimeEntryUpdate(BaseModel):
    """
    Time entry update request model with optional fields
    """
    employee_id: Optional[UUID] = Field(None, description="Change employee assignment")
    date: Optional[date_type] = Field(None, description="Change work date")
    hours: Optional[float] = Field(None, ge=0.1, le=24.0, description="Update hours worked")
    description: Optional[str] = Field(None, min_length=10, max_length=1000, description="Update description")
    billable: Optional[bool] = Field(None, description="Update billable status")

    @validator('date')
    def validate_date_not_future(cls, v):
        if v and v > date_type.today():
            raise ValueError('Date cannot be in the future')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "hours": 7.5,
                "description": "Updated work description with additional details",
                "billable": True
            }
        }


class EmployeeInfo(BaseModel):
    """Employee information in time entry responses"""
    id: UUID
    name: str
    department: str


class TimeEntryResponse(BaseModel):
    """
    Time entry response model

    Spring Boot equivalent:
    public class TimeEntryResponse {
        private UUID id;
        private LocalDate date;
        private BigDecimal hours;
        private String description;
        private Boolean billable;
        private EmployeeInfo employee;
        private LocalDateTime createdAt;
        private LocalDateTime updatedAt;
    }
    """
    id: UUID
    date: date_type
    hours: float
    description: str
    billable: bool
    employee: EmployeeInfo
    created_at: date_type
    updated_at: date_type

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "12345678-1234-5678-9abc-123456789012",
                "date": "2023-12-01",
                "hours": 8.0,
                "description": "Worked on client project specifications and requirements gathering",
                "billable": True,
                "employee": {
                    "id": "87654321-4321-8765-dcba-210987654321",
                    "name": "John Doe",
                    "department": "Corporate Law"
                },
                "created_at": "2023-12-01",
                "updated_at": "2023-12-01"
            }
        }


class TimeEntryListResponse(BaseModel):
    """Paginated time entry list response"""
    time_entries: List[TimeEntryResponse]
    pagination: Dict[str, Any]


class TimeEntrySummaryResponse(BaseModel):
    """Time entry summary/analytics response"""
    total_hours: float
    billable_hours: float
    non_billable_hours: float
    total_entries: int
    billable_percentage: float
    date_range: Dict[str, Optional[str]]
    employee: Optional[EmployeeInfo] = None
    department_breakdown: Optional[List[Dict[str, Any]]] = None


# Dependency injection for service layer
def get_time_entry_service(db: Session = Depends(get_db)) -> TimeEntryService:
    """Get time entry service with repository dependencies"""
    time_entry_repo = TimeEntryRepository(db)
    employee_repo = EmployeeRepository(db)
    return TimeEntryService(time_entry_repo, employee_repo)


# API Endpoints

@router.post("/", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_time_entry(
    time_entry_data: TimeEntryCreate,
    service: TimeEntryService = Depends(get_time_entry_service)
):
    """
    Create new time entry

    Creates a new time entry with validation and business rules:
    - Employee must exist
    - Date cannot be in the future
    - Hours must be between 0.1 and 24.0
    - Description must be at least 10 characters
    - Billable time requires detailed description (20+ chars)
    - One entry per employee per day
    """
    time_entry = service.create_time_entry(
        employee_id=time_entry_data.employee_id,
        date=time_entry_data.date,
        hours=time_entry_data.hours,
        description=time_entry_data.description,
        billable=time_entry_data.billable
    )

    return TimeEntryResponse(
        id=time_entry.id,
        date=time_entry.date,
        hours=float(time_entry.hours),
        description=time_entry.description,
        billable=time_entry.billable,
        employee=EmployeeInfo(
            id=time_entry.employee.id,
            name=time_entry.employee.name,
            department=time_entry.employee.department.name if time_entry.employee.department else "Unknown"
        ),
        created_at=time_entry.created_at.date(),
        updated_at=time_entry.updated_at.date()
    )


@router.get("/", response_model=TimeEntryListResponse)
async def list_time_entries(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    employee_id: Optional[UUID] = Query(None, description="Filter by employee ID"),
    start_date: Optional[date_type] = Query(None, description="Filter from date"),
    end_date: Optional[date_type] = Query(None, description="Filter to date"),
    billable: Optional[bool] = Query(None, description="Filter by billable status"),
    department: Optional[str] = Query(None, description="Filter by employee department"),
    search: Optional[str] = Query(None, description="Search in descriptions"),
    sort_by: str = Query("date", description="Sort by field (date, hours, created_at)"),
    service: TimeEntryService = Depends(get_time_entry_service)
):
    """
    Get paginated list of time entries with filtering

    Supports comprehensive filtering and sorting:
    - Employee filtering
    - Date range filtering
    - Billable status filtering
    - Department filtering
    - Description search
    - Flexible sorting
    """
    skip = (page - 1) * limit

    result = service.get_time_entries(
        skip=skip,
        limit=limit,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        billable=billable,
        department=department,
        search=search,
        sort_by=sort_by
    )

    # Transform to response format
    time_entries = [
        TimeEntryResponse(
            id=entry.id,
            date=entry.date,
            hours=float(entry.hours),
            description=entry.description,
            billable=entry.billable,
            employee=EmployeeInfo(
                id=entry.employee.id,
                name=entry.employee.name,
                department=entry.employee.department.name if entry.employee.department else "Unknown"
            ),
            created_at=entry.created_at.date(),
            updated_at=entry.updated_at.date()
        )
        for entry in result["time_entries"]
    ]

    return TimeEntryListResponse(
        time_entries=time_entries,
        pagination=result["pagination"]
    )


@router.get("/summary", response_model=TimeEntrySummaryResponse)
async def get_time_entries_summary(
    employee_id: Optional[UUID] = Query(None, description="Filter by employee"),
    start_date: Optional[date_type] = Query(None, description="Filter from date"),
    end_date: Optional[date_type] = Query(None, description="Filter to date"),
    group_by: Optional[str] = Query(None, description="Group by field (department)"),
    service: TimeEntryService = Depends(get_time_entry_service)
):
    """
    Get time entries summary and analytics

    Provides aggregated statistics:
    - Total hours worked
    - Billable vs non-billable breakdown
    - Billable percentage
    - Optional department breakdown
    - Employee-specific summaries
    """
    summary = service.get_time_entries_summary(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )

    return TimeEntrySummaryResponse(**summary)


@router.get("/search", response_model=List[TimeEntryResponse])
async def search_time_entries(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    service: TimeEntryService = Depends(get_time_entry_service)
):
    """
    Search time entries by description

    Full-text search in time entry descriptions for finding specific work items.
    Useful for tracking work on specific projects or clients.
    """
    time_entries = service.search_time_entries(query=q, limit=limit)

    return [
        TimeEntryResponse(
            id=entry.id,
            date=entry.date,
            hours=float(entry.hours),
            description=entry.description,
            billable=entry.billable,
            employee=EmployeeInfo(
                id=entry.employee.id,
                name=entry.employee.name,
                department=entry.employee.department.name if entry.employee.department else "Unknown"
            ),
            created_at=entry.created_at.date(),
            updated_at=entry.updated_at.date()
        )
        for entry in time_entries
    ]


@router.get("/{time_entry_id}", response_model=TimeEntryResponse)
async def get_time_entry(
    time_entry_id: UUID,
    service: TimeEntryService = Depends(get_time_entry_service)
):
    """
    Get time entry by ID

    Retrieves a specific time entry with employee and department information.
    """
    time_entry = service.get_time_entry_by_id(time_entry_id)

    return TimeEntryResponse(
        id=time_entry.id,
        date=time_entry.date,
        hours=float(time_entry.hours),
        description=time_entry.description,
        billable=time_entry.billable,
        employee=EmployeeInfo(
            id=time_entry.employee.id,
            name=time_entry.employee.name,
            department=time_entry.employee.department.name if time_entry.employee.department else "Unknown"
        ),
        created_at=time_entry.created_at.date(),
        updated_at=time_entry.updated_at.date()
    )


@router.put("/{time_entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(
    time_entry_id: UUID,
    time_entry_data: TimeEntryUpdate,
    service: TimeEntryService = Depends(get_time_entry_service)
):
    """
    Update time entry

    Updates an existing time entry with validation:
    - Partial updates allowed
    - Same business rules as creation apply
    - Cannot create duplicates (one entry per employee per day)
    """
    time_entry = service.update_time_entry(
        time_entry_id=time_entry_id,
        date=time_entry_data.date,
        hours=time_entry_data.hours,
        description=time_entry_data.description,
        billable=time_entry_data.billable,
        employee_id=time_entry_data.employee_id
    )

    return TimeEntryResponse(
        id=time_entry.id,
        date=time_entry.date,
        hours=float(time_entry.hours),
        description=time_entry.description,
        billable=time_entry.billable,
        employee=EmployeeInfo(
            id=time_entry.employee.id,
            name=time_entry.employee.name,
            department=time_entry.employee.department.name if time_entry.employee.department else "Unknown"
        ),
        created_at=time_entry.created_at.date(),
        updated_at=time_entry.updated_at.date()
    )


@router.delete("/{time_entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_entry(
    time_entry_id: UUID,
    service: TimeEntryService = Depends(get_time_entry_service)
):
    """
    Delete time entry (soft delete)

    Soft deletes a time entry to preserve audit trail and billing history.
    The entry becomes inaccessible through normal APIs but remains in database.
    """
    service.delete_time_entry(time_entry_id)