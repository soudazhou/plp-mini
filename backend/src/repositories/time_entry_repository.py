"""
TimeEntry Repository Implementation
T045 - TimeEntry repository for time tracking data access

Repository pattern for TimeEntry model data access layer.
Provides abstraction over database operations for time entry entities.

Spring Boot equivalent:
public interface TimeEntryRepository extends JpaRepository<TimeEntry, UUID> {
    List<TimeEntry> findByEmployeeIdAndDateBetween(UUID employeeId, LocalDate start, LocalDate end);
    List<TimeEntry> findByDateBetweenAndBillable(LocalDate start, LocalDate end, Boolean billable);
    BigDecimal sumHoursByEmployeeIdAndDateBetween(UUID employeeId, LocalDate start, LocalDate end);
}
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, asc, or_, case

from models.time_entry import TimeEntry
from models.employee import Employee
from models.department import Department
from repositories.base_repository import BaseRepository


class TimeEntryRepository(BaseRepository[TimeEntry]):
    """
    Repository for TimeEntry entity operations

    Provides CRUD operations and time entry-specific queries for reporting
    and analytics. Follows the Repository pattern to abstract database access.
    """

    def __init__(self, db: Session):
        super().__init__(db, TimeEntry)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        employee_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        billable: Optional[bool] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "date",
        sort_desc: bool = True
    ) -> List[TimeEntry]:
        """
        Get time entries with advanced filtering and sorting

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            employee_id: Filter by specific employee
            start_date: Filter entries from this date onwards
            end_date: Filter entries up to this date
            billable: Filter by billable status
            department: Filter by employee's department
            search: Search in description text
            sort_by: Field to sort by (date, hours, created_at)
            sort_desc: Whether to sort in descending order

        Returns:
            List of time entries matching the criteria
        """
        query = self.db.query(TimeEntry).options(
            joinedload(TimeEntry.employee).joinedload(Employee.department)
        )

        # Apply filters
        if employee_id:
            query = query.filter(TimeEntry.employee_id == employee_id)

        if start_date:
            query = query.filter(TimeEntry.date >= start_date)

        if end_date:
            query = query.filter(TimeEntry.date <= end_date)

        if billable is not None:
            query = query.filter(TimeEntry.billable == billable)

        if department:
            query = query.join(Employee).join(Department).filter(
                Department.name.ilike(f"%{department}%")
            )

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(TimeEntry.description.ilike(search_pattern))

        # Apply sorting
        if sort_by == "date":
            sort_field = TimeEntry.date
        elif sort_by == "hours":
            sort_field = TimeEntry.hours
        elif sort_by == "created_at":
            sort_field = TimeEntry.created_at
        else:
            sort_field = TimeEntry.date

        if sort_desc:
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))

        return query.offset(skip).limit(limit).all()

    def find_by_employee(
        self,
        employee_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[TimeEntry]:
        """
        Find time entries for a specific employee

        Args:
            employee_id: Employee to get entries for
            start_date: Optional start date filter
            end_date: Optional end date filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of time entries for the employee
        """
        query = self.db.query(TimeEntry).filter(
            and_(
                TimeEntry.employee_id == employee_id,
                True
            )
        )

        if start_date:
            query = query.filter(TimeEntry.date >= start_date)

        if end_date:
            query = query.filter(TimeEntry.date <= end_date)

        return query.order_by(desc(TimeEntry.date)).offset(skip).limit(limit).all()

    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        billable: Optional[bool] = None
    ) -> List[TimeEntry]:
        """
        Find time entries within a date range

        Args:
            start_date: Start of date range
            end_date: End of date range
            billable: Optional filter by billable status

        Returns:
            List of time entries in the date range
        """
        query = self.db.query(TimeEntry).filter(
            and_(
                TimeEntry.date >= start_date,
                TimeEntry.date <= end_date,
                True
            )
        )

        if billable is not None:
            query = query.filter(TimeEntry.billable == billable)

        return query.order_by(desc(TimeEntry.date)).all()

    def get_hours_summary(
        self,
        employee_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get summary of hours worked

        Args:
            employee_id: Optional filter by employee
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with hours summary
        """
        query = self.db.query(
            func.sum(TimeEntry.hours).label('total_hours'),
            func.sum(case((TimeEntry.billable == True, TimeEntry.hours), else_=0)).label('billable_hours'),
            func.sum(case((TimeEntry.billable == False, TimeEntry.hours), else_=0)).label('non_billable_hours'),
            func.count(TimeEntry.id).label('total_entries')
        ).filter(True)

        if employee_id:
            query = query.filter(TimeEntry.employee_id == employee_id)

        if start_date:
            query = query.filter(TimeEntry.date >= start_date)

        if end_date:
            query = query.filter(TimeEntry.date <= end_date)

        result = query.first()

        total_hours = float(result.total_hours) if result.total_hours else 0.0
        billable_hours = float(result.billable_hours) if result.billable_hours else 0.0
        non_billable_hours = float(result.non_billable_hours) if result.non_billable_hours else 0.0

        return {
            "total_hours": total_hours,
            "billable_hours": billable_hours,
            "non_billable_hours": non_billable_hours,
            "total_entries": result.total_entries or 0,
            "billable_percentage": (billable_hours / total_hours * 100) if total_hours > 0 else 0.0
        }

    def get_department_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get hours summary by department

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of department summaries
        """
        query = self.db.query(
            Department.name.label('department'),
            func.sum(TimeEntry.hours).label('total_hours'),
            func.sum(func.case([(TimeEntry.billable == True, TimeEntry.hours)], else_=0)).label('billable_hours'),
            func.count(TimeEntry.id).label('total_entries')
        ).join(Employee).join(Department).filter(
            True
        )

        if start_date:
            query = query.filter(TimeEntry.date >= start_date)

        if end_date:
            query = query.filter(TimeEntry.date <= end_date)

        query = query.group_by(Department.name).order_by(desc(func.sum(TimeEntry.hours)))

        results = query.all()

        return [
            {
                "department": result.department,
                "total_hours": float(result.total_hours) if result.total_hours else 0.0,
                "billable_hours": float(result.billable_hours) if result.billable_hours else 0.0,
                "total_entries": result.total_entries or 0
            }
            for result in results
        ]

    def search_by_description(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[TimeEntry]:
        """
        Search time entries by description text

        Args:
            search_term: Text to search for in descriptions
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of time entries matching the search term
        """
        search_pattern = f"%{search_term}%"

        return self.db.query(TimeEntry).options(
            joinedload(TimeEntry.employee)
        ).filter(
            and_(
                TimeEntry.description.ilike(search_pattern),
                True
            )
        ).order_by(desc(TimeEntry.date)).offset(skip).limit(limit).all()

    def get_daily_totals(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get daily hour totals for an employee

        Args:
            employee_id: Employee to get totals for
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of daily totals
        """
        query = self.db.query(
            TimeEntry.date,
            func.sum(TimeEntry.hours).label('total_hours'),
            func.sum(func.case([(TimeEntry.billable == True, TimeEntry.hours)], else_=0)).label('billable_hours')
        ).filter(
            and_(
                TimeEntry.employee_id == employee_id,
                TimeEntry.date >= start_date,
                TimeEntry.date <= end_date,
                True
            )
        ).group_by(TimeEntry.date).order_by(TimeEntry.date)

        results = query.all()

        return [
            {
                "date": result.date.isoformat(),
                "total_hours": float(result.total_hours) if result.total_hours else 0.0,
                "billable_hours": float(result.billable_hours) if result.billable_hours else 0.0
            }
            for result in results
        ]

    def check_duplicate_entry(
        self,
        employee_id: UUID,
        date: date,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if employee already has time entry for a specific date

        Args:
            employee_id: Employee to check
            date: Date to check
            exclude_id: Entry ID to exclude from check (for updates)

        Returns:
            True if duplicate exists, False otherwise
        """
        query = self.db.query(TimeEntry).filter(
            and_(
                TimeEntry.employee_id == employee_id,
                TimeEntry.date == date,
                True
            )
        )

        if exclude_id:
            query = query.filter(TimeEntry.id != exclude_id)

        return query.first() is not None

    def get_recent_entries(
        self,
        employee_id: UUID,
        limit: int = 5
    ) -> List[TimeEntry]:
        """
        Get recent time entries for an employee

        Args:
            employee_id: Employee to get entries for
            limit: Maximum number of entries to return

        Returns:
            List of recent time entries
        """
        return self.db.query(TimeEntry).filter(
            and_(
                TimeEntry.employee_id == employee_id,
                True
            )
        ).order_by(desc(TimeEntry.date), desc(TimeEntry.created_at)).limit(limit).all()

    def count_entries(
        self,
        employee_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        billable: Optional[bool] = None
    ) -> int:
        """
        Count time entries with filters

        Args:
            employee_id: Optional filter by employee
            start_date: Optional start date filter
            end_date: Optional end date filter
            billable: Optional filter by billable status

        Returns:
            Number of matching time entries
        """
        query = self.db.query(TimeEntry).filter(True)

        if employee_id:
            query = query.filter(TimeEntry.employee_id == employee_id)

        if start_date:
            query = query.filter(TimeEntry.date >= start_date)

        if end_date:
            query = query.filter(TimeEntry.date <= end_date)

        if billable is not None:
            query = query.filter(TimeEntry.billable == billable)

        return query.count()