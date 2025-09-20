"""
Employee Repository

Data access layer for employee operations with advanced querying capabilities.
Demonstrates complex repository patterns with relationships and filtering.
"""

import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from models.employee import Employee
from models.department import Department


class EmployeeRepository:
    """Repository for Employee entity data access."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create(self, employee: Employee) -> Employee:
        """Create a new employee."""
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def get_by_id(self, employee_id: uuid.UUID) -> Optional[Employee]:
        """Get employee by ID with department relationship loaded."""
        return (
            self.db.query(Employee)
            .options(joinedload(Employee.department))
            .filter(Employee.id == employee_id, Employee.deleted_at.is_(None))
            .first()
        )

    def get_by_email(self, email: str) -> Optional[Employee]:
        """Get employee by email address."""
        return (
            self.db.query(Employee)
            .filter(Employee.email == email, Employee.deleted_at.is_(None))
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        department_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[Employee]:
        """
        Get all employees with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            department_id: Filter by department
            search: Search in name or email
            include_deleted: Include soft-deleted employees
        """
        query = self.db.query(Employee).options(joinedload(Employee.department))

        # Apply soft delete filter
        if not include_deleted:
            query = query.filter(Employee.deleted_at.is_(None))

        # Apply department filter
        if department_id:
            query = query.filter(Employee.department_id == department_id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.name.ilike(search_pattern),
                    Employee.email.ilike(search_pattern)
                )
            )

        return (
            query
            .order_by(Employee.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(
        self,
        department_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """Count employees with filters."""
        query = self.db.query(Employee)

        if not include_deleted:
            query = query.filter(Employee.deleted_at.is_(None))

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.name.ilike(search_pattern),
                    Employee.email.ilike(search_pattern)
                )
            )

        return query.count()

    def update(self, employee: Employee) -> Employee:
        """Update existing employee."""
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def soft_delete(self, employee_id: uuid.UUID) -> bool:
        """Soft delete employee by ID."""
        employee = self.get_by_id(employee_id)
        if employee and not employee.is_deleted:
            employee.soft_delete()
            self.db.commit()
            return True
        return False

    def restore(self, employee_id: uuid.UUID) -> bool:
        """Restore soft-deleted employee."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )
        if employee and employee.is_deleted:
            employee.restore()
            self.db.commit()
            return True
        return False

    def exists_by_email(self, email: str, exclude_id: Optional[uuid.UUID] = None) -> bool:
        """Check if employee with email exists."""
        query = self.db.query(Employee).filter(
            Employee.email == email,
            Employee.deleted_at.is_(None)
        )

        if exclude_id:
            query = query.filter(Employee.id != exclude_id)

        return query.first() is not None

    def get_by_department(self, department_id: uuid.UUID) -> List[Employee]:
        """Get all employees in a department."""
        return (
            self.db.query(Employee)
            .filter(
                Employee.department_id == department_id,
                Employee.deleted_at.is_(None)
            )
            .order_by(Employee.name)
            .all()
        )

    def get_hired_between(self, start_date: date, end_date: date) -> List[Employee]:
        """Get employees hired between dates."""
        return (
            self.db.query(Employee)
            .filter(
                and_(
                    Employee.hire_date >= start_date,
                    Employee.hire_date <= end_date,
                    Employee.deleted_at.is_(None)
                )
            )
            .order_by(Employee.hire_date.desc())
            .all()
        )

    def get_department_statistics(self) -> List[dict]:
        """Get employee count by department."""
        return (
            self.db.query(
                Department.name.label("department_name"),
                func.count(Employee.id).label("employee_count")
            )
            .join(Department)
            .filter(Employee.deleted_at.is_(None))
            .group_by(Department.id, Department.name)
            .order_by(Department.name)
            .all()
        )