"""
Contract Test: POST /api/v1/time-entries

This test validates the API contract for creating new time entries.
Critical for time tracking functionality.
"""

import pytest
from fastapi import status


class TestTimeEntryPostContract:
    """Contract tests for POST /api/v1/time-entries endpoint."""

    @pytest.mark.contract
    def test_create_time_entry_success(self, client, sample_employee, auth_headers):
        """Test successful time entry creation."""
        from tests.conftest import TestDataFactory

        time_entry_data = TestDataFactory.time_entry_data(
            employee_id=sample_employee.id,
            hours=7.5,
            description="Contract review for ABC Corp merger",
            billable=True,
            matter_code="ABC-001"
        )

        response = client.post(
            "/api/v1/time-entries",
            json=time_entry_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify response schema
        data = response.json()
        assert "id" in data
        assert data["employee_id"] == str(sample_employee.id)
        assert data["hours"] == 7.5
        assert data["description"] == time_entry_data["description"]
        assert data["billable"] == time_entry_data["billable"]
        assert data["matter_code"] == time_entry_data["matter_code"]
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.contract
    def test_create_time_entry_validation_errors(self, client, sample_employee, auth_headers):
        """Test validation errors for time entry creation."""
        from datetime import date, timedelta

        test_cases = [
            # Invalid hours (negative)
            {
                "data": {
                    "employee_id": str(sample_employee.id),
                    "date": date.today().isoformat(),
                    "hours": -1.0,
                    "description": "Invalid negative hours",
                    "billable": True
                },
                "expected_field": "hours"
            },
            # Invalid hours (too many)
            {
                "data": {
                    "employee_id": str(sample_employee.id),
                    "date": date.today().isoformat(),
                    "hours": 25.0,
                    "description": "Too many hours in a day",
                    "billable": True
                },
                "expected_field": "hours"
            },
            # Future date
            {
                "data": {
                    "employee_id": str(sample_employee.id),
                    "date": (date.today() + timedelta(days=1)).isoformat(),
                    "hours": 8.0,
                    "description": "Future work description",
                    "billable": True
                },
                "expected_field": "date"
            },
            # Description too short
            {
                "data": {
                    "employee_id": str(sample_employee.id),
                    "date": date.today().isoformat(),
                    "hours": 8.0,
                    "description": "Short",  # Less than 10 characters
                    "billable": True
                },
                "expected_field": "description"
            }
        ]

        for test_case in test_cases:
            response = client.post(
                "/api/v1/time-entries",
                json=test_case["data"],
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            error_data = response.json()
            assert "error" in error_data
            assert "details" in error_data

    @pytest.mark.contract
    def test_create_time_entry_unauthorized(self, client, sample_employee):
        """Test unauthorized access returns 401."""
        from tests.conftest import TestDataFactory

        time_entry_data = TestDataFactory.time_entry_data(employee_id=sample_employee.id)

        response = client.post(
            "/api/v1/time-entries",
            json=time_entry_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED