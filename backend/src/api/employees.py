"""
Employee API Endpoints

FastAPI router implementation for employee management operations.
Educational comparison between FastAPI routing and Spring Boot REST controllers.

FastAPI approach:
- APIRouter for modular route organization
- Pydantic models for request/response validation
- Dependency injection via Depends()
- Automatic OpenAPI documentation generation

Spring Boot equivalent:
@RestController
@RequestMapping("/api/v1/employees")
@Validated
public class EmployeeController {
    @Autowired
    private EmployeeService employeeService;

    @PostMapping
    public ResponseEntity<Employee> createEmployee(@Valid @RequestBody CreateEmployeeRequest request) {
        // Implementation
    }
}
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.orm import Session

from database import get_db
from services.employee_service import EmployeeService


# Pydantic models for request/response validation
# Similar to Spring Boot DTOs with Bean Validation annotations

class EmployeeBase(BaseModel):
    """Base employee model with common fields."""
    name: str = Field(min_length=2, max_length=100, description="Full name of the employee")
    email: EmailStr = Field(description="Email address (must be unique)")
    hire_date: date = Field(description="Date of hire")

    @validator("hire_date")
    def validate_hire_date(cls, v):
        """Validate hire date is not in the future."""
        if v > date.today():
            raise ValueError("Hire date cannot be in the future")
        return v


class EmployeeCreate(EmployeeBase):
    """
    Employee creation request model.

    Spring Boot equivalent:
    public class CreateEmployeeRequest {
        @NotBlank
        @Size(min = 2, max = 100)
        private String name;

        @Email
        @NotBlank
        private String email;

        @NotNull
        private UUID departmentId;

        @PastOrPresent
        private LocalDate hireDate;
    }
    """
    department_id: uuid.UUID = Field(description="Department identifier")


class EmployeeUpdate(BaseModel):
    """Employee update request model with optional fields."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    department_id: Optional[uuid.UUID] = None
    hire_date: Optional[date] = None

    @validator("hire_date")
    def validate_hire_date(cls, v):
        if v and v > date.today():
            raise ValueError("Hire date cannot be in the future")
        return v


class EmployeeResponse(EmployeeBase):
    """
    Employee response model.

    Spring Boot equivalent:
    public class EmployeeResponse {
        private UUID id;
        private String name;
        private String email;
        private String department;
        private LocalDate hireDate;
        private LocalDateTime createdAt;
        private LocalDateTime updatedAt;
    }
    """
    id: uuid.UUID
    department: str = Field(description="Department name")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class EmployeeListResponse(BaseModel):
    """Paginated employee list response."""
    employees: List[EmployeeResponse]
    pagination: dict


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


# Create FastAPI router
# Similar to Spring Boot @RequestMapping
router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)


def get_employee_service(db: Session = Depends(get_db)) -> EmployeeService:
    """
    Dependency injection for EmployeeService.

    Spring Boot equivalent:
    @Autowired
    private EmployeeService employeeService;
    """
    return EmployeeService(db)


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new employee",
    description="Create a new employee record with department assignment"
)
async def create_employee(
    employee_data: EmployeeCreate,
    service: EmployeeService = Depends(get_employee_service)
) -> EmployeeResponse:
    """
    Create a new employee.

    Spring Boot equivalent:
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public EmployeeResponse createEmployee(@Valid @RequestBody CreateEmployeeRequest request) {
        Employee employee = employeeService.createEmployee(request);
        return employeeMapper.toResponse(employee);
    }
    """
    try:
        employee = service.create_employee(
            name=employee_data.name,
            email=employee_data.email,
            department_id=employee_data.department_id,
            hire_date=employee_data.hire_date
        )

        # Convert to response model
        return EmployeeResponse(
            id=employee.id,
            name=employee.name,
            email=employee.email,
            department=employee.department.name,
            hire_date=employee.hire_date,
            created_at=employee.created_at,
            updated_at=employee.updated_at
        )

    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e


@router.get(
    "/",
    response_model=EmployeeListResponse,
    summary="List employees",
    description="Get paginated list of employees with optional filtering"
)
async def list_employees(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    department: Optional[str] = Query(None, description="Filter by department name"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    service: EmployeeService = Depends(get_employee_service)
) -> EmployeeListResponse:
    """
    Get paginated list of employees.

    Spring Boot equivalent:
    @GetMapping
    public Page<EmployeeResponse> getEmployees(
        @PageableDefault(size = 20) Pageable pageable,
        @RequestParam(required = false) String department,
        @RequestParam(required = false) String search) {
        return employeeService.getEmployees(pageable, department, search);
    }
    """
    # Convert page number to skip offset
    skip = (page - 1) * limit

    # Resolve department name to ID if provided
    department_id = None
    if department:
        # This would need department service to resolve name to ID
        # For now, we'll skip this feature
        pass

    # Get employees from service
    result = service.get_employees(
        skip=skip,
        limit=limit,
        department_id=department_id,
        search=search
    )

    # Convert employees to response models
    employee_responses = [
        EmployeeResponse(
            id=emp.id,
            name=emp.name,
            email=emp.email,
            department=emp.department.name,
            hire_date=emp.hire_date,
            created_at=emp.created_at,
            updated_at=emp.updated_at
        )
        for emp in result["employees"]
    ]

    return EmployeeListResponse(
        employees=employee_responses,
        pagination=result["pagination"]
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee by ID",
    description="Retrieve a specific employee by their unique identifier"
)
async def get_employee(
    employee_id: uuid.UUID,
    service: EmployeeService = Depends(get_employee_service)
) -> EmployeeResponse:
    """
    Get employee by ID.

    Spring Boot equivalent:
    @GetMapping("/{id}")
    public EmployeeResponse getEmployee(@PathVariable UUID id) {
        Employee employee = employeeService.getEmployeeById(id);
        return employeeMapper.toResponse(employee);
    }
    """
    employee = service.get_employee_by_id(employee_id)

    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        email=employee.email,
        department=employee.department.name,
        hire_date=employee.hire_date,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee",
    description="Update an existing employee's information"
)
async def update_employee(
    employee_id: uuid.UUID,
    employee_data: EmployeeUpdate,
    service: EmployeeService = Depends(get_employee_service)
) -> EmployeeResponse:
    """
    Update employee information.

    Spring Boot equivalent:
    @PutMapping("/{id}")
    public EmployeeResponse updateEmployee(
        @PathVariable UUID id,
        @Valid @RequestBody UpdateEmployeeRequest request) {
        // Implementation
    }
    """
    employee = service.update_employee(
        employee_id=employee_id,
        name=employee_data.name,
        email=employee_data.email,
        department_id=employee_data.department_id,
        hire_date=employee_data.hire_date
    )

    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        email=employee.email,
        department=employee.department.name,
        hire_date=employee.hire_date,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete employee",
    description="Soft delete an employee (preserves historical data)"
)
async def delete_employee(
    employee_id: uuid.UUID,
    service: EmployeeService = Depends(get_employee_service)
) -> None:
    """
    Delete (soft delete) an employee.

    Spring Boot equivalent:
    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteEmployee(@PathVariable UUID id) {
        employeeService.deleteEmployee(id);
    }
    """
    service.delete_employee(employee_id)


@router.get(
    "/search",
    response_model=List[EmployeeResponse],
    summary="Search employees",
    description="Search employees using Elasticsearch (advanced search)"
)
async def search_employees(
    q: str = Query(min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    service: EmployeeService = Depends(get_employee_service)
) -> List[EmployeeResponse]:
    """
    Advanced employee search.

    This endpoint would integrate with Elasticsearch for full-text search.
    For now, it uses basic database search.

    Spring Boot equivalent:
    @GetMapping("/search")
    public List<EmployeeResponse> searchEmployees(
        @RequestParam String q,
        @RequestParam(defaultValue = "10") int limit) {
        return employeeSearchService.search(q, limit);
    }
    """
    employees = service.search_employees(q, limit)

    return [
        EmployeeResponse(
            id=emp.id,
            name=emp.name,
            email=emp.email,
            department=emp.department.name,
            hire_date=emp.hire_date,
            created_at=emp.created_at,
            updated_at=emp.updated_at
        )
        for emp in employees
    ]


# Educational Notes: FastAPI vs Spring Boot REST API
#
# 1. Route Definition:
#    FastAPI: @router.post() with decorators
#    Spring Boot: @PostMapping annotations
#
# 2. Request Validation:
#    FastAPI: Pydantic models with automatic validation
#    Spring Boot: @Valid annotations with Bean Validation
#
# 3. Response Models:
#    FastAPI: response_model parameter with Pydantic
#    Spring Boot: Return type with @ResponseBody (implicit)
#
# 4. Dependency Injection:
#    FastAPI: Depends() parameter with provider functions
#    Spring Boot: @Autowired fields or constructor injection
#
# 5. Error Handling:
#    FastAPI: HTTPException with structured details
#    Spring Boot: @ExceptionHandler methods
#
# 6. Documentation:
#    FastAPI: Automatic OpenAPI/Swagger generation
#    Spring Boot: SpringDoc or manual Swagger configuration
#
# 7. Status Codes:
#    FastAPI: status_code parameter in decorators
#    Spring Boot: @ResponseStatus annotations
#
# Both frameworks provide:
# - Automatic request/response serialization
# - Built-in validation
# - Structured error handling
# - API documentation generation
# - Dependency injection
# - Modular route organization