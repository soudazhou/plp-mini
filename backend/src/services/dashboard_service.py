"""
Dashboard Analytics Service

Provides business intelligence and analytics for the law firm dashboard.
Educational comparison between SQLAlchemy aggregation queries and
Spring Boot JPA aggregate functions.

Spring Boot equivalent:
@Service
@Transactional(readOnly = true)
public class DashboardService {
    @Autowired
    private TimeEntryRepository timeEntryRepository;

    @Autowired
    private EmployeeRepository employeeRepository;

    public DashboardOverview getOverview() {
        // Implementation with JPA aggregate functions
    }
}
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, extract, func, case
from sqlalchemy.orm import Session

from models.department import Department
from models.employee import Employee
from models.time_entry import TimeEntry
from repositories.department_repository import DepartmentRepository
from repositories.employee_repository import EmployeeRepository
from repositories.time_entry_repository import TimeEntryRepository


class DashboardService:
    """
    Dashboard analytics service providing firm-wide metrics.

    Educational comparison:
    - SQLAlchemy: Manual aggregation with func.sum(), func.count()
    - Spring Boot: @Query with aggregate functions or Criteria API
    """

    def __init__(self, db: Session):
        self.db = db
        self.employee_repo = EmployeeRepository(db)
        self.time_entry_repo = TimeEntryRepository(db)
        self.department_repo = DepartmentRepository(db)

    def get_overview(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
        """
        Get dashboard overview with key metrics.

        Spring Boot equivalent:
        @Query("SELECT new com.firm.dto.DashboardOverview(" +
               "COUNT(DISTINCT e), " +
               "SUM(te.hours), " +
               "SUM(CASE WHEN te.billable = true THEN te.hours ELSE 0 END), " +
               "AVG(CASE WHEN te.billable = true THEN te.hours ELSE 0 END) / AVG(te.hours) * 100) " +
               "FROM Employee e LEFT JOIN e.timeEntries te " +
               "WHERE te.date BETWEEN :startDate AND :endDate")
        DashboardOverview getOverview(@Param("startDate") LocalDate start,
                                    @Param("endDate") LocalDate end);
        """
        # Default to current month if no date range provided
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)

        if not end_date:
            end_date = date.today()

        # Total employees count
        total_employees = self.employee_repo.count()

        # Time entry aggregations for the date range
        time_query = self.db.query(
            func.sum(TimeEntry.hours).label('total_hours'),
            func.sum(
                case(
                    (TimeEntry.billable == True, TimeEntry.hours),
                    else_=0
                )
            ).label('billable_hours'),
            func.count(TimeEntry.id).label('total_entries')
        ).filter(
            and_(
                TimeEntry.date >= start_date,
                TimeEntry.date <= end_date
            )
        ).first()

        total_hours = float(time_query.total_hours or 0)
        billable_hours = float(time_query.billable_hours or 0)
        total_entries = time_query.total_entries or 0

        # Calculate utilization rate
        utilization_rate = (billable_hours / total_hours * 100) if total_hours > 0 else 0

        # Average hours per employee
        avg_hours_per_employee = total_hours / total_employees if total_employees > 0 else 0

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": {
                "total_employees": total_employees,
                "total_hours": round(total_hours, 2),
                "billable_hours": round(billable_hours, 2),
                "non_billable_hours": round(total_hours - billable_hours, 2),
                "utilization_rate": round(utilization_rate, 1),
                "total_entries": total_entries,
                "avg_hours_per_employee": round(avg_hours_per_employee, 2)
            }
        }

    def get_department_hours(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict]:
        """
        Get hours breakdown by department for charts.

        Spring Boot equivalent:
        @Query("SELECT new com.firm.dto.DepartmentHours(" +
               "d.name, " +
               "SUM(te.hours), " +
               "SUM(CASE WHEN te.billable = true THEN te.hours ELSE 0 END)) " +
               "FROM Department d " +
               "LEFT JOIN d.employees e " +
               "LEFT JOIN e.timeEntries te " +
               "WHERE te.date BETWEEN :startDate AND :endDate " +
               "GROUP BY d.id, d.name " +
               "ORDER BY SUM(te.hours) DESC")
        List<DepartmentHours> getDepartmentHours(@Param("startDate") LocalDate start,
                                               @Param("endDate") LocalDate end);
        """
        # Default to current month
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)

        if not end_date:
            end_date = date.today()

        # Query department hours with SQLAlchemy joins and aggregations
        dept_hours = self.db.query(
            Department.name,
            func.coalesce(func.sum(TimeEntry.hours), 0).label('total_hours'),
            func.coalesce(
                func.sum(
                    case(
                        (TimeEntry.billable == True, TimeEntry.hours),
                        else_=0
                    )
                ), 0
            ).label('billable_hours'),
            func.count(Employee.id).label('employee_count')
        ).outerjoin(Employee, Department.id == Employee.department_id)\
         .outerjoin(
            TimeEntry,
            and_(
                Employee.id == TimeEntry.employee_id,
                TimeEntry.date >= start_date,
                TimeEntry.date <= end_date
            )
         ).group_by(Department.id, Department.name)\
         .order_by(func.sum(TimeEntry.hours).desc()).all()

        return [
            {
                "department": dept.name,
                "total_hours": float(dept.total_hours),
                "billable_hours": float(dept.billable_hours),
                "non_billable_hours": float(dept.total_hours - dept.billable_hours),
                "employee_count": dept.employee_count,
                "utilization_rate": round(
                    (dept.billable_hours / dept.total_hours * 100) if dept.total_hours > 0 else 0,
                    1
                )
            }
            for dept in dept_hours
        ]

    def get_utilization_rates(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict]:
        """
        Get utilization rates by employee.

        Spring Boot equivalent would use window functions or subqueries:
        @Query("SELECT new com.firm.dto.EmployeeUtilization(" +
               "e.name, " +
               "SUM(te.hours), " +
               "SUM(CASE WHEN te.billable = true THEN te.hours ELSE 0 END), " +
               "SUM(CASE WHEN te.billable = true THEN te.hours ELSE 0 END) / SUM(te.hours) * 100) " +
               "FROM Employee e " +
               "LEFT JOIN e.timeEntries te " +
               "WHERE te.date BETWEEN :startDate AND :endDate " +
               "GROUP BY e.id, e.name " +
               "HAVING SUM(te.hours) > 0 " +
               "ORDER BY SUM(CASE WHEN te.billable = true THEN te.hours ELSE 0 END) / SUM(te.hours) DESC")
        """
        # Default to current month
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)

        if not end_date:
            end_date = date.today()

        # Query employee utilization rates
        employee_util = self.db.query(
            Employee.name,
            Employee.email,
            Department.name.label('department_name'),
            func.coalesce(func.sum(TimeEntry.hours), 0).label('total_hours'),
            func.coalesce(
                func.sum(
                    case(
                        (TimeEntry.billable == True, TimeEntry.hours),
                        else_=0
                    )
                ), 0
            ).label('billable_hours')
        ).join(Department, Employee.department_id == Department.id)\
         .outerjoin(
            TimeEntry,
            and_(
                Employee.id == TimeEntry.employee_id,
                TimeEntry.date >= start_date,
                TimeEntry.date <= end_date
            )
         ).group_by(Employee.id, Employee.name, Employee.email, Department.name)\
         .having(func.sum(TimeEntry.hours) > 0)\
         .order_by(func.sum(TimeEntry.hours).desc()).all()

        return [
            {
                "employee": emp.name,
                "email": emp.email,
                "department": emp.department_name,
                "total_hours": float(emp.total_hours),
                "billable_hours": float(emp.billable_hours),
                "non_billable_hours": float(emp.total_hours - emp.billable_hours),
                "utilization_rate": round(
                    (emp.billable_hours / emp.total_hours * 100) if emp.total_hours > 0 else 0,
                    1
                )
            }
            for emp in employee_util
        ]

    def get_trends(self, days: int = 30) -> Dict:
        """
        Get time tracking trends over the specified number of days.

        Spring Boot equivalent would use date functions:
        @Query("SELECT DATE(te.date) as workDate, " +
               "SUM(te.hours) as totalHours, " +
               "SUM(CASE WHEN te.billable = true THEN te.hours ELSE 0 END) as billableHours " +
               "FROM TimeEntry te " +
               "WHERE te.date >= :startDate " +
               "GROUP BY DATE(te.date) " +
               "ORDER BY DATE(te.date)")
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Daily aggregations for trend analysis
        daily_trends = self.db.query(
            TimeEntry.date,
            func.sum(TimeEntry.hours).label('total_hours'),
            func.sum(
                case(
                    (TimeEntry.billable == True, TimeEntry.hours),
                    else_=0
                )
            ).label('billable_hours'),
            func.count(TimeEntry.id).label('entry_count')
        ).filter(
            and_(
                TimeEntry.date >= start_date,
                TimeEntry.date <= end_date
            )
        ).group_by(TimeEntry.date)\
         .order_by(TimeEntry.date).all()

        # Calculate weekly averages
        total_days = len(daily_trends) if daily_trends else 1
        total_hours_period = sum(day.total_hours for day in daily_trends)
        total_billable_period = sum(day.billable_hours for day in daily_trends)

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "trends": [
                {
                    "date": day.date.isoformat(),
                    "total_hours": float(day.total_hours),
                    "billable_hours": float(day.billable_hours),
                    "non_billable_hours": float(day.total_hours - day.billable_hours),
                    "entry_count": day.entry_count,
                    "utilization_rate": round(
                        (day.billable_hours / day.total_hours * 100) if day.total_hours > 0 else 0,
                        1
                    )
                }
                for day in daily_trends
            ],
            "averages": {
                "daily_total_hours": round(total_hours_period / total_days, 2),
                "daily_billable_hours": round(total_billable_period / total_days, 2),
                "period_utilization_rate": round(
                    (total_billable_period / total_hours_period * 100) if total_hours_period > 0 else 0,
                    1
                )
            }
        }


# Educational Notes: Dashboard Service Design
#
# 1. Aggregation Patterns:
#    SQLAlchemy: func.sum(), func.count(), func.case() for conditional aggregation
#    Spring Boot: @Query with SUM(), COUNT(), CASE WHEN expressions
#
# 2. Performance Considerations:
#    - Proper indexing on date and foreign key columns
#    - Consider materialized views for complex aggregations
#    - Caching for frequently accessed dashboard data
#
# 3. Business Logic Placement:
#    - Calculations in service layer vs database
#    - Domain-specific formatting and rounding
#    - Error handling for edge cases (zero divisions)
#
# 4. Query Optimization:
#    - LEFT JOIN vs INNER JOIN for optional relationships
#    - HAVING clause for aggregate filtering
#    - ORDER BY for consistent result ordering
#
# 5. Data Transfer Objects:
#    - Structured response formats for frontend consumption
#    - Consistent field naming and data types
#    - ISO date formatting for API responses