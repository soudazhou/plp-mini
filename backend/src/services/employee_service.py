"""
Employee Service

Business logic layer for employee operations.
Educational comparison between service layer patterns in FastAPI and Spring Boot.

FastAPI approach:
- Service classes with dependency injection
- Manual transaction management
- Pydantic models for validation
- Exception handling with HTTP status codes

Spring Boot equivalent:
@Service
@Transactional
public class EmployeeService {
    @Autowired
    private EmployeeRepository employeeRepository;

    public Employee createEmployee(CreateEmployeeRequest request) {
        // Business logic implementation
    }
}
"""

import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.employee import Employee
from models.department import Department
from repositories.employee_repository import EmployeeRepository
from repositories.department_repository import DepartmentRepository


class EmployeeService:
    """
    Service layer for employee business logic.

    Handles complex business operations, validation, and coordination
    between multiple repositories. Similar to Spring Boot @Service classes.

    Spring Boot equivalent:
    @Service
    @Transactional
    public class EmployeeService {
        private final EmployeeRepository employeeRepository;
        private final DepartmentRepository departmentRepository;

        public EmployeeService(EmployeeRepository employeeRepo,
                              DepartmentRepository deptRepo) {
            this.employeeRepository = employeeRepo;
            this.departmentRepository = deptRepo;
        }
    }
    """

    def __init__(self, db_session: Session):
        """
        Initialize service with database session.

        In production, this would use dependency injection framework.
        FastAPI equivalent uses Depends() for automatic injection.

        Spring Boot equivalent:
        @Autowired
        public EmployeeService(EmployeeRepository repo) {
            this.employeeRepository = repo;
        }
        """
        self.db = db_session
        self.employee_repo = EmployeeRepository(db_session)
        self.department_repo = DepartmentRepository(db_session)

    def create_employee(
        self,
        name: str,
        email: str,
        department_id: uuid.UUID,
        hire_date: date
    ) -> Employee:
        """
        Create a new employee with business validation.

        Spring Boot equivalent:
        @Transactional
        public Employee createEmployee(CreateEmployeeRequest request) {
            // Validation logic
            // Save operation
            // Event publishing
        }
        """
        # Business validation: Check if email already exists
        if self.employee_repo.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": f"Employee with email {email} already exists",
                    "code": "EMAIL_ALREADY_EXISTS",
                    "field": "email"
                }
            )

        # Business validation: Check if department exists
        department = self.department_repo.get_by_id(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Department with ID {department_id} not found",
                    "code": "DEPARTMENT_NOT_FOUND",
                    "field": "department_id"
                }
            )

        # Business validation: Check hire date is not in future
        if hire_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Hire date cannot be in the future",
                    "code": "INVALID_HIRE_DATE",
                    "field": "hire_date"
                }
            )

        # Create employee
        employee = Employee(
            name=name,
            email=email,
            department_id=department_id,
            hire_date=hire_date
        )

        try:
            return self.employee_repo.create(employee)
        except Exception as e:
            # Log error and convert to business exception
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create employee"
            ) from e

    def get_employee_by_id(self, employee_id: uuid.UUID) -> Employee:
        """
        Get employee by ID with error handling.

        Spring Boot equivalent:
        public Employee getEmployeeById(UUID id) {
            return employeeRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Employee not found"));
        }
        """
        employee = self.employee_repo.get_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": f"Employee with ID {employee_id} not found",
                    "code": "EMPLOYEE_NOT_FOUND"
                }
            )
        return employee

    def get_employees(
        self,
        skip: int = 0,
        limit: int = 20,
        department_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None
    ) -> dict:
        """
        Get paginated list of employees with filtering.

        Returns both data and pagination metadata.

        Spring Boot equivalent:
        public Page<Employee> getEmployees(Pageable pageable,
                                          EmployeeFilter filter) {
            return employeeRepository.findAll(filter.toSpecification(), pageable);
        }
        """
        # Validate pagination parameters
        if skip < 0:
            skip = 0
        if limit < 1 or limit > 100:
            limit = 20

        # Get employees and count
        employees = self.employee_repo.get_all(
            skip=skip,
            limit=limit,
            department_id=department_id,
            search=search
        )

        total_count = self.employee_repo.count(
            department_id=department_id,
            search=search
        )

        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit
        current_page = (skip // limit) + 1

        return {
            "employees": employees,
            "pagination": {
                "page": current_page,
                "limit": limit,
                "total": total_count,
                "pages": total_pages
            }
        }

    def update_employee(
        self,
        employee_id: uuid.UUID,
        name: Optional[str] = None,
        email: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        hire_date: Optional[date] = None
    ) -> Employee:
        """
        Update employee with partial updates and validation.

        Spring Boot equivalent:
        @Transactional
        public Employee updateEmployee(UUID id, UpdateEmployeeRequest request) {
            Employee employee = getEmployeeById(id);
            // Apply updates with validation
            return employeeRepository.save(employee);
        }
        """
        # Get existing employee
        employee = self.get_employee_by_id(employee_id)

        # Validate email uniqueness if email is being updated
        if email and email != employee.email:
            if self.employee_repo.exists_by_email(email, exclude_id=employee_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": f"Employee with email {email} already exists",
                        "code": "EMAIL_ALREADY_EXISTS",
                        "field": "email"
                    }
                )

        # Validate department if being updated
        if department_id and department_id != employee.department_id:
            department = self.department_repo.get_by_id(department_id)
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": f"Department with ID {department_id} not found",
                        "code": "DEPARTMENT_NOT_FOUND",
                        "field": "department_id"
                    }
                )

        # Validate hire date
        if hire_date and hire_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Hire date cannot be in the future",
                    "code": "INVALID_HIRE_DATE",
                    "field": "hire_date"
                }
            )

        # Apply updates
        if name is not None:
            employee.name = name
        if email is not None:
            employee.email = email
        if department_id is not None:
            employee.department_id = department_id
        if hire_date is not None:
            employee.hire_date = hire_date

        return self.employee_repo.update(employee)

    def delete_employee(self, employee_id: uuid.UUID) -> bool:
        """
        Soft delete an employee.

        Business rule: Employees with time entries cannot be hard deleted.
        Use soft delete to preserve historical data integrity.

        Spring Boot equivalent:
        @Transactional
        public void deleteEmployee(UUID id) {
            Employee employee = getEmployeeById(id);
            // Check business constraints
            employee.markAsDeleted();
            employeeRepository.save(employee);
        }
        """
        # Check if employee exists
        employee = self.get_employee_by_id(employee_id)

        # Business validation: Check if employee has time entries
        # In a real system, this would check for related data
        # For now, we'll just perform soft delete

        success = self.employee_repo.soft_delete(employee_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee could not be deleted"
            )

        return success

    def search_employees(self, query: str, limit: int = 10) -> List[Employee]:
        """
        Search employees by name or email.

        This is a simple implementation. In production, this would
        integrate with Elasticsearch for advanced search capabilities.

        Spring Boot equivalent:
        public List<Employee> searchEmployees(String query) {
            return employeeSearchRepository.findByNameOrEmail(query);
        }
        """
        if not query or len(query.strip()) < 2:
            return []

        return self.employee_repo.get_all(
            skip=0,
            limit=limit,
            search=query.strip()
        )

    def get_department_statistics(self) -> List[dict]:
        """
        Get employee statistics by department.

        Business logic for dashboard analytics.

        Spring Boot equivalent:
        public List<DepartmentStatistics> getDepartmentStatistics() {
            return employeeRepository.getDepartmentStatistics();
        }
        """
        return self.employee_repo.get_department_statistics()

    def get_recent_hires(self, days: int = 30) -> List[Employee]:
        """
        Get employees hired in the last N days.

        Business logic for HR dashboard.
        """
        from datetime import timedelta

        start_date = date.today() - timedelta(days=days)
        end_date = date.today()

        return self.employee_repo.get_hired_between(start_date, end_date)


# Educational Notes: Service Layer Patterns
#
# 1. Business Logic Placement:
#    FastAPI: Service classes with explicit validation
#    Spring Boot: @Service beans with @Transactional methods
#
# 2. Exception Handling:
#    FastAPI: HTTPException with structured error details
#    Spring Boot: Custom exceptions with @ExceptionHandler
#
# 3. Validation Strategy:
#    FastAPI: Manual validation in service methods
#    Spring Boot: Bean Validation annotations + custom validators
#
# 4. Transaction Management:
#    FastAPI: Manual session commit/rollback
#    Spring Boot: @Transactional annotation with automatic management
#
# 5. Dependency Injection:
#    FastAPI: Constructor injection with Depends()
#    Spring Boot: @Autowired fields or constructor injection
#
# 6. Error Response Format:
#    FastAPI: Structured JSON with error codes
#    Spring Boot: @ExceptionHandler with ResponseEntity
#
# Both approaches provide:
# - Separation of business logic from data access
# - Consistent error handling
# - Input validation and sanitization
# - Transaction boundary management
# - Testable business operations