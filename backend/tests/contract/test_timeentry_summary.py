"""
Contract Test: GET /api/v1/time-entries/summary
T027 - Time entry summary endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the time entry summary/analytics endpoint specification.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestTimeEntrySummaryContract:
    """Contract tests for time entry summary endpoint"""

    def test_get_time_entries_summary_success(self, client: TestClient, auth_headers):
        """
        Test successful time entries summary retrieval

        Contract specification:
        - Path: GET /api/v1/time-entries/summary
        - Returns: 200 OK with TimeEntrySummaryResponse
        - Auth: Required
        """
        response = client.get("/api/v1/time-entries/summary", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        summary_data = response.json()
        required_fields = [
            "total_hours", "billable_hours", "non_billable_hours",
            "total_entries", "billable_percentage", "date_range"
        ]
        for field in required_fields:
            assert field in summary_data

    def test_get_time_entries_summary_date_range_filter(self, client: TestClient, auth_headers):
        """
        Test summary with date range filter

        Contract specification:
        - Should support start_date and end_date parameters
        """
        from datetime import date, timedelta

        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/time-entries/summary?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        summary_data = response.json()
        assert "date_range" in summary_data
        assert summary_data["date_range"]["start"] == start_date
        assert summary_data["date_range"]["end"] == end_date

    def test_get_time_entries_summary_employee_filter(self, client: TestClient, sample_employee, auth_headers):
        """
        Test summary filtered by employee

        Contract specification:
        - Should support employee_id filter parameter
        """
        response = client.get(
            f"/api/v1/time-entries/summary?employee_id={sample_employee['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        summary_data = response.json()
        assert "employee" in summary_data
        assert summary_data["employee"]["id"] == sample_employee["id"]

    def test_get_time_entries_summary_department_breakdown(self, client: TestClient, auth_headers):
        """
        Test summary with department breakdown

        Contract specification:
        - Should support group_by=department parameter
        """
        response = client.get(
            "/api/v1/time-entries/summary?group_by=department",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        summary_data = response.json()
        assert "department_breakdown" in summary_data
        assert isinstance(summary_data["department_breakdown"], list)

        if len(summary_data["department_breakdown"]) > 0:
            dept_summary = summary_data["department_breakdown"][0]
            assert "department" in dept_summary
            assert "total_hours" in dept_summary
            assert "billable_hours" in dept_summary

    def test_get_time_entries_summary_unauthorized(self, client: TestClient):
        """
        Test unauthorized access

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        response = client.get("/api/v1/time-entries/summary")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_time_entries_summary_calculations(self, client: TestClient, auth_headers):
        """
        Test summary calculations accuracy

        Contract specification:
        - total_hours = billable_hours + non_billable_hours
        - billable_percentage = (billable_hours / total_hours) * 100
        """
        response = client.get("/api/v1/time-entries/summary", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        summary_data = response.json()
        total_hours = summary_data["total_hours"]
        billable_hours = summary_data["billable_hours"]
        non_billable_hours = summary_data["non_billable_hours"]
        billable_percentage = summary_data["billable_percentage"]

        # Verify calculations
        assert total_hours == billable_hours + non_billable_hours

        if total_hours > 0:
            expected_percentage = (billable_hours / total_hours) * 100
            assert abs(billable_percentage - expected_percentage) < 0.01  # Allow for rounding