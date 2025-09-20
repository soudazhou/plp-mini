"""
Department Model

Represents organizational divisions within the law firm.
This is a simple lookup entity with one-to-many relationship to employees.

Educational comparison between SQLAlchemy model definition and
JPA Entity class with relationship mapping.
"""

from typing import List

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDAuditMixin


class Department(Base, UUIDAuditMixin):
    """
    Department entity representing law firm organizational divisions.

    JPA equivalent:
    @Entity
    @Table(name = "departments")
    public class Department extends AuditableEntity {
        @Column(nullable = false, unique = true, length = 50)
        private String name;

        @Column(length = 200)
        private String description;

        @OneToMany(mappedBy = "department", cascade = CascadeType.ALL)
        private List<Employee> employees = new ArrayList<>();
    }
    """

    __tablename__ = "departments"

    # Core fields
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Department name (unique)",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Department description",
    )

    # Relationships
    # Note: Using string reference to avoid circular imports
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="select",  # Default loading strategy
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Department(id={self.id}, name='{self.name}')>"

    @property
    def employee_count(self) -> int:
        """
        Get the number of employees in this department.

        In a production application, this might be calculated
        via a database query to avoid loading all employees.
        """
        return len(self.employees)


# Educational Notes: Department Model Design
#
# 1. Simplicity by Design:
#    - Minimal fields focused on core functionality
#    - Clear business purpose as organizational unit
#    - Avoids over-engineering with unnecessary complexity
#
# 2. Relationship Mapping:
#    SQLAlchemy: relationship() with back_populates
#    JPA: @OneToMany with mappedBy
#
# 3. Lazy Loading Strategy:
#    SQLAlchemy: lazy="select" (default N+1 queries)
#    JPA: FetchType.LAZY (default for collections)
#
# 4. Cascade Operations:
#    SQLAlchemy: cascade="all, delete-orphan"
#    JPA: CascadeType.ALL with orphanRemoval=true
#
# 5. Indexing Strategy:
#    - name field indexed for lookup performance
#    - unique constraint prevents duplicate departments
#    - Consider adding indexes on frequently queried fields
#
# 6. Business Logic:
#    - employee_count as computed property
#    - Could be moved to service layer for better separation
#    - Database aggregation would be more efficient for large datasets