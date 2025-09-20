"""
Department Service
T046 - Department business logic service

Provides business logic for department management including
CRUD operations and departmental analytics.

Spring Boot equivalent:
@Service
@Transactional
public class DepartmentService {
    @Autowired
    private DepartmentRepository departmentRepository;

    public Department createDepartment(CreateDepartmentRequest request) { ... }
    public List<Department> getAllDepartments() { ... }
}
"""

from typing import List, Optional
from uuid import UUID

from repositories.department_repository import DepartmentRepository
from models.department import Department


class DepartmentService:
    """
    Department business logic service.

    Educational comparison:
    - SQLAlchemy: Manual service layer with repository injection
    - Spring Boot: @Service with @Autowired repository dependencies
    """

    def __init__(self, department_repo: DepartmentRepository):
        self.department_repo = department_repo

    def create_department(self, name: str, description: str = None) -> Department:
        """
        Create a new department.

        Business rules:
        - Department name must be unique
        - Name must be non-empty and trimmed

        Spring Boot equivalent:
        @Transactional
        public Department createDepartment(String name, String description) {
            if (departmentRepository.existsByName(name)) {
                throw new BusinessException("Department already exists");
            }
            Department dept = new Department(name.trim(), description);
            return departmentRepository.save(dept);
        }
        """
        if not name or not name.strip():
            raise ValueError("Department name cannot be empty")

        name = name.strip()

        # Check for existing department
        existing = self.department_repo.get_by_name(name)
        if existing:
            raise ValueError(f"Department '{name}' already exists")

        return self.department_repo.create(name=name, description=description)

    def get_all_departments(self) -> List[Department]:
        """Get all departments."""
        return self.department_repo.get_all()

    def get_department_by_id(self, department_id: UUID) -> Department:
        """
        Get department by ID.

        Args:
            department_id: Department UUID

        Returns:
            Department entity

        Raises:
            ValueError: If department not found
        """
        department = self.department_repo.get_by_id(department_id)
        if not department:
            raise ValueError(f"Department {department_id} not found")
        return department

    def update_department(self, department_id: UUID, name: str = None,
                         description: str = None) -> Department:
        """
        Update department details.

        Business rules:
        - Updated name must be unique (if provided)
        - At least one field must be provided for update

        Spring Boot equivalent:
        @Transactional
        public Department updateDepartment(UUID id, UpdateDepartmentRequest request) {
            Department dept = departmentRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Department not found"));

            if (request.getName() != null) {
                validateUniqueName(request.getName(), id);
                dept.setName(request.getName());
            }
            return departmentRepository.save(dept);
        }
        """
        if not name and description is None:
            raise ValueError("At least one field must be provided for update")

        department = self.get_department_by_id(department_id)

        # Check name uniqueness if updating name
        if name and name.strip() != department.name:
            name = name.strip()
            existing = self.department_repo.get_by_name(name)
            if existing and existing.id != department_id:
                raise ValueError(f"Department '{name}' already exists")

        return self.department_repo.update(
            department_id,
            name=name.strip() if name else None,
            description=description
        )

    def delete_department(self, department_id: UUID) -> None:
        """
        Delete department.

        Business rules:
        - Cannot delete department with employees
        - Soft delete to preserve historical data

        Spring Boot equivalent:
        @Transactional
        public void deleteDepartment(UUID id) {
            Department dept = departmentRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Department not found"));

            if (dept.getEmployees().size() > 0) {
                throw new BusinessException("Cannot delete department with employees");
            }

            departmentRepository.softDelete(id);
        }
        """
        department = self.get_department_by_id(department_id)

        # Check for employees in department
        employee_count = self.department_repo.count_employees(department_id)
        if employee_count > 0:
            raise ValueError(f"Cannot delete department with {employee_count} employees")

        self.department_repo.delete(department_id)

    def get_department_with_employees(self, department_id: UUID) -> Department:
        """
        Get department with its employees loaded.

        Educational note:
        - SQLAlchemy: Explicit eager loading with joinedload
        - Spring Boot: @EntityGraph or fetch joins
        """
        return self.department_repo.get_with_employees(department_id)

    def get_department_statistics(self, department_id: UUID) -> dict:
        """
        Get department statistics including employee count and time tracking metrics.

        Returns:
            Dictionary with department stats:
            - employee_count: Number of employees
            - total_hours_this_month: Hours logged this month
            - avg_utilization: Average utilization rate
        """
        department = self.get_department_by_id(department_id)

        stats = self.department_repo.get_department_stats(department_id)

        return {
            "department": {
                "id": str(department.id),
                "name": department.name,
                "description": department.description
            },
            "employee_count": stats.get("employee_count", 0),
            "total_hours_this_month": stats.get("total_hours", 0.0),
            "avg_utilization": stats.get("avg_utilization", 0.0),
            "active_employees": stats.get("active_employees", 0)
        }


# Educational Notes: Department Service Design
#
# 1. Business Logic Placement:
#    - Validation rules in service layer
#    - Database operations delegated to repository
#    - Complex business rules handled here
#
# 2. Error Handling:
#    - ValueError for business rule violations
#    - Clear error messages for user feedback
#    - Early validation before database operations
#
# 3. Transactional Boundaries:
#    - Service methods define transaction scope
#    - Repository operations are atomic
#    - Complex operations use single transactions
#
# 4. Dependency Injection:
#    - Repository injected via constructor
#    - Allows for testing with mock repositories
#    - Similar to Spring Boot @Autowired pattern
#
# 5. Data Transfer:
#    - Service returns domain objects (Department)
#    - Statistics return structured dictionaries
#    - API layer handles response formatting