"""
TimeEntry Model

Represents billable work logged by employees with matter details
and time spent. This is the core entity for time tracking analytics.

Educational comparison between SQLAlchemy decimal handling and
JPA BigDecimal precision for financial calculations.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import Base, UUIDAuditMixin


class TimeEntry(Base, UUIDAuditMixin):
    """
    Time entry entity for billable hours tracking.

    JPA equivalent:
    @Entity
    @Table(name = "time_entries")
    public class TimeEntry extends AuditableEntity {
        @ManyToOne(fetch = FetchType.LAZY)
        @JoinColumn(name = "employee_id", nullable = false)
        private Employee employee;

        @Column(nullable = false)
        private LocalDate date;

        @Column(nullable = false, precision = 5, scale = 2)
        private BigDecimal hours;

        @Column(nullable = false, length = 500)
        private String description;

        @Column(nullable = false)
        private Boolean billable = true;

        @Column(length = 20)
        private String matterCode;
    }
    """

    __tablename__ = "time_entries"

    # Foreign key relationships
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Employee who logged the time",
    )

    # Core time entry fields
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date when work was performed",
    )

    hours: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),  # Max 999.99 hours
        nullable=False,
        comment="Hours worked (decimal with 2-digit precision)",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Description of work performed",
    )

    billable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,  # Index for billable vs non-billable queries
        comment="Whether time is billable to client",
    )

    matter_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,  # Index for matter-based reporting
        comment="Matter or case code (optional)",
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="time_entries",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<TimeEntry(id={self.id}, employee_id={self.employee_id}, "
            f"date={self.date}, hours={self.hours})>"
        )

    @validates("hours")
    def validate_hours(self, key: str, value: Decimal) -> Decimal:
        """
        Validate hours field constraints.

        SQLAlchemy validators vs JPA Bean Validation:

        JPA equivalent:
        @Min(value = 0, message = "Hours must be positive")
        @Max(value = 24, message = "Hours cannot exceed 24 per day")
        @Digits(integer = 3, fraction = 2, message = "Invalid hours format")
        private BigDecimal hours;
        """
        if value is None:
            raise ValueError("Hours cannot be null")

        if value <= 0:
            raise ValueError("Hours must be greater than 0")

        if value > 24:
            raise ValueError("Hours cannot exceed 24 per day")

        # Ensure precision (max 2 decimal places)
        if value.as_tuple().exponent < -2:
            raise ValueError("Hours precision cannot exceed 2 decimal places")

        return value

    @validates("date")
    def validate_date(self, key: str, value: date) -> date:
        """
        Validate date constraints.

        Business rule: Cannot log time for future dates.
        """
        if value is None:
            raise ValueError("Date cannot be null")

        if value > date.today():
            raise ValueError("Cannot log time for future dates")

        return value

    @validates("description")
    def validate_description(self, key: str, value: str) -> str:
        """
        Validate description field.

        Business rule: Minimum 10 characters for meaningful descriptions.
        """
        if not value or not value.strip():
            raise ValueError("Description cannot be empty")

        if len(value.strip()) < 10:
            raise ValueError("Description must be at least 10 characters")

        if len(value) > 500:
            raise ValueError("Description cannot exceed 500 characters")

        return value.strip()

    @validates("matter_code")
    def validate_matter_code(self, key: str, value: Optional[str]) -> Optional[str]:
        """
        Validate matter code format.

        Expected format: ABC-123 or ABC-123-DEF
        """
        if value is None or value.strip() == "":
            return None

        value = value.strip().upper()

        # Simple regex validation for matter code format
        import re

        pattern = r"^[A-Z]{2,4}-\d{1,4}(-[A-Z]{1,3})?$"
        if not re.match(pattern, value):
            raise ValueError(
                "Matter code must follow format: ABC-123 or ABC-123-DEF"
            )

        return value

    @property
    def is_weekend(self) -> bool:
        """Check if the time entry was logged on a weekend."""
        return self.date.weekday() >= 5  # Saturday = 5, Sunday = 6

    @property
    def hours_float(self) -> float:
        """Convert hours to float for calculations."""
        return float(self.hours)

    def get_billing_amount(self, hourly_rate: Decimal) -> Decimal:
        """
        Calculate billing amount for this time entry.

        Only calculates for billable entries.
        In a real system, rates would be stored per employee or matter.

        JPA equivalent:
        public BigDecimal getBillingAmount(BigDecimal hourlyRate) {
            if (!billable) {
                return BigDecimal.ZERO;
            }
            return hours.multiply(hourlyRate);
        }
        """
        if not self.billable:
            return Decimal("0.00")

        return self.hours * hourly_rate

    @classmethod
    def get_daily_total_for_employee(
        cls, session, employee_id: uuid.UUID, target_date: date
    ) -> Decimal:
        """
        Get total hours logged by employee for a specific date.

        Used for validation to prevent logging more than 24 hours per day.

        JPA equivalent:
        @Query("SELECT SUM(te.hours) FROM TimeEntry te WHERE te.employee.id = :employeeId AND te.date = :date")
        BigDecimal getDailyTotalForEmployee(@Param("employeeId") UUID employeeId, @Param("date") LocalDate date);
        """
        from sqlalchemy import func

        result = (
            session.query(func.sum(cls.hours))
            .filter(cls.employee_id == employee_id, cls.date == target_date)
            .scalar()
        )

        return result or Decimal("0.00")

    @classmethod
    def get_monthly_stats(
        cls, session, employee_id: uuid.UUID, year: int, month: int
    ) -> dict:
        """
        Get monthly statistics for an employee.

        Returns total hours, billable hours, and utilization rate.
        """
        from sqlalchemy import and_, extract, func

        # Query for monthly totals
        stats = (
            session.query(
                func.sum(cls.hours).label("total_hours"),
                func.sum(
                    func.case((cls.billable.is_(True), cls.hours), else_=0)
                ).label("billable_hours"),
                func.count(cls.id).label("entry_count"),
            )
            .filter(
                and_(
                    cls.employee_id == employee_id,
                    extract("year", cls.date) == year,
                    extract("month", cls.date) == month,
                )
            )
            .first()
        )

        total_hours = stats.total_hours or Decimal("0.00")
        billable_hours = stats.billable_hours or Decimal("0.00")
        entry_count = stats.entry_count or 0

        # Calculate utilization rate
        utilization_rate = Decimal("0.00")
        if total_hours > 0:
            utilization_rate = (billable_hours / total_hours) * 100

        return {
            "total_hours": total_hours,
            "billable_hours": billable_hours,
            "non_billable_hours": total_hours - billable_hours,
            "entry_count": entry_count,
            "utilization_rate": utilization_rate,
        }


# Educational Notes: TimeEntry Model Design
#
# 1. Decimal Precision for Financial Data:
#    SQLAlchemy: Numeric(precision=5, scale=2) for exact decimal arithmetic
#    JPA: @Column(precision=5, scale=2) with BigDecimal type
#    Avoids floating-point precision issues in financial calculations
#
# 2. Validation Strategies:
#    SQLAlchemy: @validates decorators with custom logic
#    JPA: Bean Validation annotations (@Min, @Max, @Pattern, etc.)
#    Both provide field-level validation before persistence
#
# 3. Business Rule Enforcement:
#    - Date validation (no future dates)
#    - Hours constraints (0.01 to 24.00)
#    - Description length requirements
#    - Matter code format validation
#
# 4. Query Optimization:
#    - Strategic indexes on frequently queried columns
#    - Composite indexes for date range queries
#    - Foreign key indexes for join performance
#
# 5. Aggregate Calculations:
#    - Class methods for common aggregations
#    - Database-level calculations for performance
#    - Avoid N+1 queries with proper query design
#
# 6. Data Integrity:
#    - CASCADE delete when employee is removed
#    - NOT NULL constraints on required fields
#    - Check constraints could be added for additional validation