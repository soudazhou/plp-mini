"""
Employee Model

Represents law firm staff members with their basic information
and departmental assignment. This is the core entity for people analytics.

Educational comparison between SQLAlchemy relationship mapping and
JPA Entity relationships with proper foreign key management.
"""

import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, UUIDAuditMixin


class Employee(Base, UUIDAuditMixin, SoftDeleteMixin):
    """
    Employee entity representing law firm staff members.

    JPA equivalent:
    @Entity
    @Table(name = "employees")
    @SQLDelete(sql = "UPDATE employees SET deleted_at = NOW() WHERE id = ?")
    @Where(clause = "deleted_at IS NULL")
    public class Employee extends AuditableEntity {
        @Column(nullable = false, length = 100)
        private String name;

        @Column(nullable = false, unique = true)
        private String email;

        @ManyToOne(fetch = FetchType.LAZY)
        @JoinColumn(name = "department_id")
        private Department department;

        @OneToMany(mappedBy = "employee", cascade = CascadeType.ALL)
        private List<TimeEntry> timeEntries = new ArrayList<>();

        @OneToOne(mappedBy = "employee")
        private User user;
    }
    """

    __tablename__ = "employees"

    # Core employee information
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Full name of the employee",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Email address (unique)",
    )

    hire_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date of hire",
    )

    # Foreign key relationships
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Department foreign key",
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="employees",
        lazy="select",  # N+1 issue potential - could use "joined"
    )

    time_entries: Mapped[List["TimeEntry"]] = relationship(
        "TimeEntry",
        back_populates="employee",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # user: Mapped[Optional["User"]] = relationship(
    #     "User",
    #     back_populates="employee",
    #     lazy="select",
    #     uselist=False,  # One-to-one relationship
    # )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Employee(id={self.id}, name='{self.name}', email='{self.email}')>"

    @property
    def years_of_service(self) -> int:
        """
        Calculate years of service based on hire date.

        Business logic in model vs service layer is debatable.
        Spring Boot would typically put this in a service method.
        """
        from datetime import date

        today = date.today()
        return today.year - self.hire_date.year - (
            (today.month, today.day) < (self.hire_date.month, self.hire_date.day)
        )

    @property
    def has_user_account(self) -> bool:
        """Check if employee has an associated user account."""
        return self.user is not None

    def get_total_hours(self, start_date: date = None, end_date: date = None) -> float:
        """
        Calculate total hours worked in a date range.

        This is a convenience method that would typically be
        implemented in the service layer for better separation of concerns.

        JPA equivalent:
        @Query("SELECT SUM(te.hours) FROM TimeEntry te WHERE te.employee = :employee " +
               "AND te.date BETWEEN :startDate AND :endDate")
        BigDecimal getTotalHours(@Param("employee") Employee employee,
                                @Param("startDate") LocalDate startDate,
                                @Param("endDate") LocalDate endDate);
        """
        filtered_entries = self.time_entries

        if start_date:
            filtered_entries = [e for e in filtered_entries if e.date >= start_date]

        if end_date:
            filtered_entries = [e for e in filtered_entries if e.date <= end_date]

        return sum(entry.hours for entry in filtered_entries)

    def get_billable_hours(
        self, start_date: date = None, end_date: date = None
    ) -> float:
        """Calculate billable hours worked in a date range."""
        filtered_entries = self.time_entries

        if start_date:
            filtered_entries = [e for e in filtered_entries if e.date >= start_date]

        if end_date:
            filtered_entries = [e for e in filtered_entries if e.date <= end_date]

        return sum(entry.hours for entry in filtered_entries if entry.billable)

    def get_utilization_rate(
        self, start_date: date = None, end_date: date = None
    ) -> float:
        """
        Calculate utilization rate (billable hours / total hours).

        Returns percentage between 0 and 100.
        """
        total_hours = self.get_total_hours(start_date, end_date)
        if total_hours == 0:
            return 0.0

        billable_hours = self.get_billable_hours(start_date, end_date)
        return (billable_hours / total_hours) * 100

    @classmethod
    def search_by_name_or_email(cls, session, query: str) -> List["Employee"]:
        """
        Search employees by name or email (case-insensitive).

        This demonstrates SQLAlchemy query patterns.
        In production, this would likely use Elasticsearch for full-text search.

        JPA equivalent:
        @Query("SELECT e FROM Employee e WHERE " +
               "LOWER(e.name) LIKE LOWER(CONCAT('%', :query, '%')) OR " +
               "LOWER(e.email) LIKE LOWER(CONCAT('%', :query, '%'))")
        List<Employee> searchByNameOrEmail(@Param("query") String query);
        """
        from sqlalchemy import or_

        return (
            session.query(cls)
            .filter(
                or_(
                    cls.name.ilike(f"%{query}%"),
                    cls.email.ilike(f"%{query}%"),
                )
            )
            .order_by(cls.name)
            .all()
        )


# Educational Notes: Employee Model Design
#
# 1. Soft Delete Implementation:
#    - Inherits from SoftDeleteMixin for logical deletion
#    - Preserves historical data for time entries
#    - Alternative to hard deletes for audit purposes
#
# 2. Relationship Loading Strategies:
#    SQLAlchemy: lazy="select" (N+1), lazy="joined" (single query)
#    JPA: FetchType.LAZY, FetchType.EAGER, @EntityGraph
#
# 3. Cascade Operations:
#    - TimeEntries deleted when employee is deleted
#    - Department restricted from deletion if employees exist
#    - Similar to JPA's CascadeType and foreign key constraints
#
# 4. Business Logic Placement:
#    - Simple calculations in model (years_of_service)
#    - Complex aggregations better suited for service layer
#    - Database queries for performance-critical operations
#
# 5. Search Functionality:
#    - Basic ILIKE queries for simple text search
#    - Production systems would use Elasticsearch
#    - Consider indexing strategies for performance
#
# 6. Validation Considerations:
#    - Email uniqueness enforced at database level
#    - Additional validation would be in Pydantic schemas
#    - JPA uses Bean Validation annotations on entity fields