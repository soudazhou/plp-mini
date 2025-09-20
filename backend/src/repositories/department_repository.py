"""
Department Repository

Data access layer for department operations using Repository pattern.
Educational comparison between SQLAlchemy Repository pattern and
Spring Data JPA repository interfaces.

SQLAlchemy approach:
- Explicit repository class with CRUD methods
- Manual query construction using Session
- Custom business queries as class methods
- Dependency injection via constructor

Spring Data JPA equivalent:
@Repository
public interface DepartmentRepository extends JpaRepository<Department, UUID> {
    Optional<Department> findByName(String name);
    List<Department> findByNameContainingIgnoreCase(String name);
}
"""

import uuid
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.department import Department


class DepartmentRepository:
    """
    Repository for Department entity data access.

    Implements Repository pattern to encapsulate data access logic
    and provide a clean API for department operations.

    Spring Data JPA equivalent:
    @Repository
    public interface DepartmentRepository extends JpaRepository<Department, UUID> {
        // Methods auto-generated from method names
        Optional<Department> findByName(String name);
        List<Department> findAllByOrderByNameAsc();
    }
    """

    def __init__(self, db_session: Session):
        """
        Initialize repository with database session.

        Spring Boot equivalent:
        @Autowired
        private EntityManager entityManager;
        """
        self.db = db_session

    def create(self, department: Department) -> Department:
        """
        Create a new department.

        Spring Data JPA equivalent:
        Department savedDepartment = departmentRepository.save(department);
        """
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def get_by_id(self, department_id: uuid.UUID) -> Optional[Department]:
        """
        Get department by ID.

        Spring Data JPA equivalent:
        Optional<Department> dept = departmentRepository.findById(id);
        """
        return (
            self.db.query(Department)
            .filter(Department.id == department_id)
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Department]:
        """
        Get department by name (case-sensitive).

        Spring Data JPA equivalent:
        Optional<Department> dept = departmentRepository.findByName(name);
        """
        return (
            self.db.query(Department)
            .filter(Department.name == name)
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Department]:
        """
        Get all departments with pagination.

        Spring Data JPA equivalent:
        Page<Department> departments = departmentRepository.findAll(
            PageRequest.of(page, size, Sort.by("name"))
        );
        """
        return (
            self.db.query(Department)
            .order_by(Department.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, department: Department) -> Department:
        """
        Update existing department.

        Spring Data JPA equivalent:
        Department updated = departmentRepository.save(department);
        """
        self.db.commit()
        self.db.refresh(department)
        return department

    def delete(self, department_id: uuid.UUID) -> bool:
        """
        Delete department by ID.

        Returns True if department was deleted, False if not found.

        Spring Data JPA equivalent:
        departmentRepository.deleteById(id);
        """
        department = self.get_by_id(department_id)
        if department:
            self.db.delete(department)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """
        Count total number of departments.

        Spring Data JPA equivalent:
        long count = departmentRepository.count();
        """
        return self.db.query(Department).count()

    def exists_by_name(self, name: str) -> bool:
        """
        Check if department with given name exists.

        Spring Data JPA equivalent:
        boolean exists = departmentRepository.existsByName(name);
        """
        return (
            self.db.query(Department)
            .filter(Department.name == name)
            .first()
            is not None
        )

    def search_by_name(self, name_pattern: str) -> List[Department]:
        """
        Search departments by name pattern (case-insensitive).

        Spring Data JPA equivalent:
        List<Department> depts = departmentRepository
            .findByNameContainingIgnoreCase(pattern);
        """
        return (
            self.db.query(Department)
            .filter(Department.name.ilike(f"%{name_pattern}%"))
            .order_by(Department.name)
            .all()
        )

    def get_department_with_employee_count(self) -> List[dict]:
        """
        Get departments with employee count.

        Custom query demonstrating JOIN and aggregation.

        Spring Data JPA equivalent:
        @Query("SELECT d.name, COUNT(e) FROM Department d LEFT JOIN d.employees e GROUP BY d.id")
        List<Object[]> getDepartmentsWithEmployeeCount();
        """
        from models.employee import Employee

        return (
            self.db.query(
                Department.name,
                Department.description,
                func.count(Employee.id).label("employee_count")
            )
            .outerjoin(Employee)
            .group_by(Department.id, Department.name, Department.description)
            .order_by(Department.name)
            .all()
        )


# Educational Notes: Repository Pattern Comparison
#
# 1. Interface Definition:
#    SQLAlchemy: Explicit class with manual method implementation
#    Spring Data JPA: Interface with auto-generated implementations
#
# 2. Query Construction:
#    SQLAlchemy: Manual query building with Session API
#    Spring Data JPA: Method name-based query generation
#
# 3. Custom Queries:
#    SQLAlchemy: Class methods with manual SQL/ORM queries
#    Spring Data JPA: @Query annotations with JPQL/native SQL
#
# 4. Transaction Management:
#    SQLAlchemy: Manual commit/rollback in repository methods
#    Spring Data JPA: @Transactional annotations on service layer
#
# 5. Dependency Injection:
#    SQLAlchemy: Constructor injection of Session
#    Spring Data JPA: @Autowired repository interfaces
#
# 6. Pagination:
#    SQLAlchemy: Manual offset/limit with total count queries
#    Spring Data JPA: Pageable parameter with Page<T> return type
#
# Both approaches provide:
# - Clean separation of data access logic
# - Testable repository interfaces
# - Custom query support
# - Type-safe database operations
# - Abstraction over ORM complexities