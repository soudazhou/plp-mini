"""
Dashboard API Endpoints

FastAPI router implementation for dashboard analytics operations.
Educational comparison between FastAPI async endpoints and
Spring Boot @RestController with reactive programming.

FastAPI approach:
- APIRouter for modular organization
- Async endpoints for non-blocking operations
- Query parameters for filtering
- Automatic OpenAPI documentation

Spring Boot equivalent:
@RestController
@RequestMapping("/api/v1/dashboard")
@CrossOrigin(origins = "*")
public class DashboardController {
    @Autowired
    private DashboardService dashboardService;

    @GetMapping("/overview")
    public ResponseEntity<DashboardOverview> getOverview(
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {
        // Implementation
    }
}
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Pydantic response models for dashboard data
# Similar to Spring Boot DTOs with Jackson serialization

class MetricsResponse(BaseModel):
    """Core dashboard metrics."""
    total_employees: int = Field(description="Total number of employees")
    total_hours: float = Field(description="Total hours worked in period")
    billable_hours: float = Field(description="Total billable hours")
    non_billable_hours: float = Field(description="Total non-billable hours")
    utilization_rate: float = Field(description="Utilization rate percentage")
    total_entries: int = Field(description="Total time entries")
    avg_hours_per_employee: float = Field(description="Average hours per employee")


class PeriodResponse(BaseModel):
    """Date period information."""
    start_date: str = Field(description="Period start date (ISO format)")
    end_date: str = Field(description="Period end date (ISO format)")


class DashboardOverviewResponse(BaseModel):
    """
    Dashboard overview response.

    Spring Boot equivalent:
    public class DashboardOverviewResponse {
        private PeriodInfo period;
        private Metrics metrics;

        // getters/setters
    }
    """
    period: PeriodResponse
    metrics: MetricsResponse

    class Config:
        json_schema_extra = {
            "example": {
                "period": {
                    "start_date": "2023-01-01",
                    "end_date": "2023-01-31"
                },
                "metrics": {
                    "total_employees": 25,
                    "total_hours": 1200.5,
                    "billable_hours": 960.0,
                    "non_billable_hours": 240.5,
                    "utilization_rate": 80.0,
                    "total_entries": 150,
                    "avg_hours_per_employee": 48.02
                }
            }
        }


class DepartmentHoursResponse(BaseModel):
    """Department hours breakdown."""
    department: str = Field(description="Department name")
    total_hours: float = Field(description="Total hours worked")
    billable_hours: float = Field(description="Billable hours")
    non_billable_hours: float = Field(description="Non-billable hours")
    employee_count: int = Field(description="Number of employees")
    utilization_rate: float = Field(description="Department utilization rate")


class EmployeeUtilizationResponse(BaseModel):
    """Employee utilization data."""
    employee: str = Field(description="Employee name")
    email: str = Field(description="Employee email")
    department: str = Field(description="Department name")
    total_hours: float = Field(description="Total hours worked")
    billable_hours: float = Field(description="Billable hours")
    non_billable_hours: float = Field(description="Non-billable hours")
    utilization_rate: float = Field(description="Utilization rate percentage")


class DailyTrendResponse(BaseModel):
    """Daily trend data point."""
    date: str = Field(description="Date (ISO format)")
    total_hours: float = Field(description="Total hours for the day")
    billable_hours: float = Field(description="Billable hours for the day")
    non_billable_hours: float = Field(description="Non-billable hours for the day")
    entry_count: int = Field(description="Number of time entries")
    utilization_rate: float = Field(description="Daily utilization rate")


class TrendAveragesResponse(BaseModel):
    """Trend period averages."""
    daily_total_hours: float = Field(description="Average daily total hours")
    daily_billable_hours: float = Field(description="Average daily billable hours")
    period_utilization_rate: float = Field(description="Period utilization rate")


class TrendPeriodResponse(BaseModel):
    """Trend period information."""
    start_date: str = Field(description="Trend start date")
    end_date: str = Field(description="Trend end date")
    days: int = Field(description="Number of days in period")


class TrendsResponse(BaseModel):
    """Time tracking trends response."""
    period: TrendPeriodResponse
    trends: list[DailyTrendResponse]
    averages: TrendAveragesResponse


# Dashboard API endpoints

@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    start_date: Optional[date] = Query(None, description="Start date for metrics (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for metrics (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview with key firm metrics.

    Returns summary statistics for the specified date range including:
    - Total employees and time entries
    - Total and billable hours
    - Utilization rates
    - Average hours per employee

    Spring Boot equivalent:
    @GetMapping("/overview")
    @Operation(summary = "Get dashboard overview")
    public ResponseEntity<DashboardOverviewResponse> getOverview(
        @RequestParam(required = false) LocalDate startDate,
        @RequestParam(required = false) LocalDate endDate) {

        DashboardOverviewResponse overview = dashboardService.getOverview(startDate, endDate);
        return ResponseEntity.ok(overview);
    }
    """
    service = DashboardService(db)
    overview_data = service.get_overview(start_date, end_date)

    return DashboardOverviewResponse(
        period=PeriodResponse(**overview_data["period"]),
        metrics=MetricsResponse(**overview_data["metrics"])
    )


@router.get("/department-hours", response_model=list[DepartmentHoursResponse])
async def get_department_hours(
    start_date: Optional[date] = Query(None, description="Start date for analysis (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get hours breakdown by department for chart visualization.

    Returns aggregated hours data for each department including:
    - Total and billable hours
    - Employee count
    - Department utilization rates

    Suitable for creating bar charts and pie charts in the frontend.

    Spring Boot equivalent:
    @GetMapping("/department-hours")
    public ResponseEntity<List<DepartmentHoursResponse>> getDepartmentHours(
        @RequestParam(required = false) LocalDate startDate,
        @RequestParam(required = false) LocalDate endDate) {

        List<DepartmentHoursResponse> data = dashboardService.getDepartmentHours(startDate, endDate);
        return ResponseEntity.ok(data);
    }
    """
    service = DashboardService(db)
    dept_data = service.get_department_hours(start_date, end_date)

    return [DepartmentHoursResponse(**dept) for dept in dept_data]


@router.get("/utilization", response_model=list[EmployeeUtilizationResponse])
async def get_utilization_rates(
    start_date: Optional[date] = Query(None, description="Start date for analysis (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get utilization rates by employee.

    Returns per-employee utilization data including:
    - Total and billable hours
    - Utilization rate calculations
    - Department assignments

    Useful for identifying high/low performers and workload distribution.

    Spring Boot equivalent:
    @GetMapping("/utilization")
    public ResponseEntity<List<EmployeeUtilizationResponse>> getUtilizationRates(
        @RequestParam(required = false) LocalDate startDate,
        @RequestParam(required = false) LocalDate endDate) {

        List<EmployeeUtilizationResponse> data = dashboardService.getUtilizationRates(startDate, endDate);
        return ResponseEntity.ok(data);
    }
    """
    service = DashboardService(db)
    util_data = service.get_utilization_rates(start_date, end_date)

    return [EmployeeUtilizationResponse(**emp) for emp in util_data]


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
    db: Session = Depends(get_db)
):
    """
    Get time tracking trends over the specified period.

    Returns daily time tracking data for trend analysis including:
    - Daily hours worked (total and billable)
    - Entry counts per day
    - Period averages and utilization trends

    Useful for creating line charts and identifying patterns.

    Spring Boot equivalent:
    @GetMapping("/trends")
    public ResponseEntity<TrendsResponse> getTrends(
        @RequestParam(defaultValue = "30") @Min(1) @Max(365) int days) {

        TrendsResponse trends = dashboardService.getTrends(days);
        return ResponseEntity.ok(trends);
    }
    """
    service = DashboardService(db)
    trend_data = service.get_trends(days)

    return TrendsResponse(
        period=TrendPeriodResponse(**trend_data["period"]),
        trends=[DailyTrendResponse(**day) for day in trend_data["trends"]],
        averages=TrendAveragesResponse(**trend_data["averages"])
    )


# Educational Notes: Dashboard API Design
#
# 1. Response Model Design:
#    - Structured DTOs for consistent API responses
#    - Field descriptions for automatic documentation
#    - Example data for Swagger UI
#
# 2. Query Parameter Validation:
#    FastAPI: Query() with validation constraints
#    Spring Boot: @RequestParam with @Valid annotations
#
# 3. Async Endpoints:
#    - FastAPI: Native async/await support
#    - Spring Boot: WebFlux reactive programming
#
# 4. Date Handling:
#    - ISO date format for API consistency
#    - Optional parameters with sensible defaults
#    - Timezone considerations for global applications
#
# 5. Error Handling:
#    - HTTP status codes for different scenarios
#    - Structured error responses
#    - Input validation and sanitization
#
# 6. Documentation:
#    - OpenAPI integration for interactive docs
#    - Comprehensive endpoint descriptions
#    - Request/response examples