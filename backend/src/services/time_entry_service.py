"""
TimeEntry Service Implementation
T049 - TimeEntry service for time tracking business logic

Service layer for time entry operations with business rules and validation.
Coordinates between API layer and repository layer.

Spring Boot equivalent:
@Service
public class TimeEntryService {
    private final TimeEntryRepository timeEntryRepository;
    private final EmployeeRepository employeeRepository;

    public TimeEntryDto createTimeEntry(CreateTimeEntryRequest request) { ... }
    public Page<TimeEntryDto> getTimeEntries(Pageable pageable, TimeEntryFilter filter) { ... }
    public Optional<TimeEntryDto> updateTimeEntry(UUID id, UpdateTimeEntryRequest request) { ... }
}
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.time_entry import TimeEntry
from models.employee import Employee
from repositories.time_entry_repository import TimeEntryRepository
from repositories.employee_repository import EmployeeRepository


class TimeEntryService:
    """
    Service for time entry business operations

    Handles time tracking logic, validation, and business rules.
    Coordinates between API and data layers.
    """

    def __init__(self, time_entry_repo: TimeEntryRepository, employee_repo: EmployeeRepository):
        self.time_entry_repo = time_entry_repo
        self.employee_repo = employee_repo

    def create_time_entry(
        self,
        employee_id: UUID,
        date: date,
        hours: float,
        description: str,
        billable: bool = False
    ) -> TimeEntry:
        """
        Create a new time entry

        Args:
            employee_id: ID of the employee
            date: Date of work
            hours: Hours worked (decimal allowed)
            description: Work description
            billable: Whether time is billable

        Returns:
            Created time entry

        Raises:
            HTTPException: If validation fails or employee not found
        """
        # Validate employee exists
        employee = self.employee_repo.find_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"Employee with ID {employee_id} not found"}
            )

        # Business rule validations
        self._validate_time_entry_data(date, hours, description, billable)

        # Check for duplicate entries (business rule: one entry per employee per date)
        if self.time_entry_repo.check_duplicate_entry(employee_id, date):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": f"Time entry already exists for employee {employee.name} on {date}",
                    "suggestion": "Update the existing entry or choose a different date"
                }
            )

        # Create time entry
        time_entry = TimeEntry(
            employee_id=employee_id,
            date=date,
            hours=Decimal(str(hours)),
            description=description,
            billable=billable
        )

        return self.time_entry_repo.create(time_entry)

    def get_time_entries(
        self,
        skip: int = 0,
        limit: int = 20,
        employee_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        billable: Optional[bool] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "date"
    ) -> Dict[str, Any]:
        """
        Get time entries with filtering and pagination

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            employee_id: Filter by employee
            start_date: Filter from date
            end_date: Filter to date
            billable: Filter by billable status
            department: Filter by department
            search: Search in descriptions
            sort_by: Field to sort by

        Returns:
            Dictionary with time entries and pagination info
        """
        # Validate pagination parameters
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Skip must be >= 0"}
            )

        if limit <= 0 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Limit must be between 1 and 100"}
            )

        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Start date must be before or equal to end date"}
            )

        # Get time entries
        time_entries = self.time_entry_repo.get_all(
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

        # Get total count for pagination
        total = self.time_entry_repo.count_entries(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            billable=billable
        )

        return {
            "time_entries": time_entries,
            "pagination": {
                "page": (skip // limit) + 1,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    def get_time_entry_by_id(self, time_entry_id: UUID) -> TimeEntry:
        """
        Get time entry by ID

        Args:
            time_entry_id: ID of time entry

        Returns:
            Time entry

        Raises:
            HTTPException: If time entry not found
        """
        time_entry = self.time_entry_repo.find_by_id(time_entry_id)
        if not time_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Time entry with ID {time_entry_id} not found"}
            )

        return time_entry

    def update_time_entry(
        self,
        time_entry_id: UUID,
        date: Optional[date] = None,
        hours: Optional[float] = None,
        description: Optional[str] = None,
        billable: Optional[bool] = None,
        employee_id: Optional[UUID] = None
    ) -> TimeEntry:
        """
        Update an existing time entry

        Args:
            time_entry_id: ID of time entry to update
            date: New date (optional)
            hours: New hours (optional)
            description: New description (optional)
            billable: New billable status (optional)
            employee_id: New employee ID (optional)

        Returns:
            Updated time entry

        Raises:
            HTTPException: If validation fails or time entry not found
        """
        # Find existing time entry
        time_entry = self.get_time_entry_by_id(time_entry_id)

        # Validate employee if changing
        if employee_id and employee_id != time_entry.employee_id:
            employee = self.employee_repo.find_by_id(employee_id)
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": f"Employee with ID {employee_id} not found"}
                )

        # Validate updated data
        final_date = date if date is not None else time_entry.date
        final_hours = hours if hours is not None else float(time_entry.hours)
        final_description = description if description is not None else time_entry.description
        final_billable = billable if billable is not None else time_entry.billable

        self._validate_time_entry_data(final_date, final_hours, final_description, final_billable)

        # Check for duplicate if date or employee changes
        final_employee_id = employee_id if employee_id is not None else time_entry.employee_id
        if (date != time_entry.date or employee_id != time_entry.employee_id):
            if self.time_entry_repo.check_duplicate_entry(
                final_employee_id, final_date, exclude_id=time_entry_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": f"Time entry already exists for this employee on {final_date}"}
                )

        # Update fields
        update_data = {}
        if date is not None:
            update_data["date"] = date
        if hours is not None:
            update_data["hours"] = Decimal(str(hours))
        if description is not None:
            update_data["description"] = description
        if billable is not None:
            update_data["billable"] = billable
        if employee_id is not None:
            update_data["employee_id"] = employee_id

        return self.time_entry_repo.update(time_entry_id, update_data)

    def delete_time_entry(self, time_entry_id: UUID) -> None:
        """
        Soft delete a time entry

        Args:
            time_entry_id: ID of time entry to delete

        Raises:
            HTTPException: If time entry not found
        """
        time_entry = self.get_time_entry_by_id(time_entry_id)
        self.time_entry_repo.soft_delete(time_entry_id)

    def get_time_entries_summary(
        self,
        employee_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get time entries summary and analytics

        Args:
            employee_id: Filter by employee
            start_date: Filter from date
            end_date: Filter to date
            group_by: Group results by field (department, employee)

        Returns:
            Summary data with totals and breakdowns
        """
        # Get basic summary
        summary = self.time_entry_repo.get_hours_summary(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date
        )

        # Add date range info
        summary["date_range"] = {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        }

        # Add employee info if filtering by specific employee
        if employee_id:
            employee = self.employee_repo.find_by_id(employee_id)
            if employee:
                summary["employee"] = {
                    "id": str(employee.id),
                    "name": employee.name,
                    "department": employee.department.name if employee.department else None
                }

        # Add breakdowns if requested
        if group_by == "department":
            summary["department_breakdown"] = self.time_entry_repo.get_department_summary(
                start_date=start_date,
                end_date=end_date
            )

        return summary

    def search_time_entries(
        self,
        query: str,
        limit: int = 10
    ) -> List[TimeEntry]:
        """
        Search time entries by description

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching time entries

        Raises:
            HTTPException: If query is too short
        """
        if len(query.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Search query must be at least 2 characters"}
            )

        if limit <= 0 or limit > 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Limit must be between 1 and 50"}
            )

        return self.time_entry_repo.search_by_description(query, limit=limit)

    def get_employee_daily_totals(
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

        Raises:
            HTTPException: If employee not found or invalid date range
        """
        # Validate employee exists
        employee = self.employee_repo.find_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Employee with ID {employee_id} not found"}
            )

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Start date must be before or equal to end date"}
            )

        return self.time_entry_repo.get_daily_totals(employee_id, start_date, end_date)

    def _validate_time_entry_data(
        self,
        date: date,
        hours: float,
        description: str,
        billable: bool
    ) -> None:
        """
        Validate time entry data according to business rules

        Args:
            date: Date of work
            hours: Hours worked
            description: Work description
            billable: Whether time is billable

        Raises:
            HTTPException: If validation fails
        """
        # Date cannot be in the future
        if date > datetime.now().date():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Time entry date cannot be in the future"}
            )

        # Hours must be positive and reasonable
        if hours <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Hours must be greater than 0"}
            )

        if hours > 24:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Hours cannot exceed 24 per day"}
            )

        # Description must be meaningful
        if len(description.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Description must be at least 10 characters"}
            )

        # Billable time requires more detailed description
        if billable and len(description.strip()) < 20:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Billable time requires detailed description (minimum 20 characters)"}
            )