"""
Contract Test: GET /api/v1/time-entries/{id}
T024 - Time entry retrieve endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the individual time entry retrieval endpoint specification.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestTimeEntryGetContract:
    """Contract tests for time entry GET by ID endpoint"""

    def test_get_time_entry_success(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test successful time entry retrieval by ID

        Contract specification:
        - Path: GET /api/v1/time-entries/{time_entry_id}
        - Returns: 200 OK with TimeEntryResponse
        - Auth: Required
        """
        response = client.get(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        assert entry_data["id"] == sample_time_entry["id"]
        assert entry_data["date"] == sample_time_entry["date"]
        assert entry_data["hours"] == sample_time_entry["hours"]
        assert entry_data["description"] == sample_time_entry["description"]
        assert entry_data["billable"] == sample_time_entry["billable"]
        assert "employee" in entry_data
        assert "created_at" in entry_data
        assert "updated_at" in entry_data

    def test_get_time_entry_not_found(self, client: TestClient, auth_headers):
        """
        Test time entry not found error

        Contract specification:
        - Returns: 404 Not Found for non-existent time entry
        """
        fake_id = "12345678-1234-5678-9abc-123456789999"
        response = client.get(f"/api/v1/time-entries/{fake_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "detail" in error_data

    def test_get_time_entry_invalid_uuid(self, client: TestClient, auth_headers):
        """
        Test invalid UUID format error

        Contract specification:
        - Returns: 422 Unprocessable Entity for invalid UUID
        """
        response = client.get("/api/v1/time-entries/invalid-uuid", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_get_time_entry_unauthorized(self, client: TestClient, sample_time_entry):
        """
        Test unauthorized access

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        response = client.get(f"/api/v1/time-entries/{sample_time_entry['id']}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_time_entry_includes_employee_info(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test that time entry includes employee information

        Contract specification:
        - Response should include employee details, not just ID
        """
        response = client.get(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        assert "employee" in entry_data
        employee = entry_data["employee"]
        assert "id" in employee
        assert "name" in employee
        assert "department" in employee
        assert isinstance(employee["name"], str)
        assert isinstance(employee["department"], str)

    def test_get_time_entry_response_schema(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test response schema matches TimeEntryResponse

        Contract specification:
        - Response must match TimeEntryResponse Pydantic model
        """
        response = client.get(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()

        # Required fields from TimeEntryResponse schema
        required_fields = [
            "id", "date", "hours", "description", "billable",
            "employee", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in entry_data, f"Missing required field: {field}"

        # Field type validations
        assert isinstance(entry_data["hours"], (int, float))
        assert isinstance(entry_data["description"], str)
        assert isinstance(entry_data["billable"], bool)
        assert entry_data["hours"] > 0
        assert len(entry_data["description"]) > 0

    def test_get_time_entry_hours_precision(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test hours field precision and formatting

        Contract specification:
        - Hours should support decimal precision (e.g., 7.5 hours)
        - Should be represented as float or decimal
        """
        response = client.get(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        hours = entry_data["hours"]
        assert isinstance(hours, (int, float))
        assert hours > 0
        assert hours <= 24  # Reasonable daily limit

    def test_get_time_entry_date_format(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test date field format

        Contract specification:
        - Date should be in ISO format (YYYY-MM-DD)
        """
        response = client.get(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        date_str = entry_data["date"]

        # Validate ISO date format
        from datetime import datetime
        try:
            datetime.fromisoformat(date_str)
        except ValueError:
            pytest.fail(f"Invalid date format: {date_str}")

    def test_get_time_entry_audit_fields(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test audit trail fields

        Contract specification:
        - Should include created_at and updated_at timestamps
        - Timestamps should be in ISO format
        """
        response = client.get(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()

        # Verify audit fields exist
        assert "created_at" in entry_data
        assert "updated_at" in entry_data

        # Validate timestamp format
        from datetime import datetime
        try:
            datetime.fromisoformat(entry_data["created_at"].replace('Z', '+00:00'))
            datetime.fromisoformat(entry_data["updated_at"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Invalid timestamp format in audit fields")

    def test_get_time_entry_soft_deleted_not_found(self, client: TestClient, soft_deleted_time_entry, auth_headers):
        """
        Test that soft-deleted time entries are not returned

        Contract specification:
        - Soft-deleted time entries should return 404 Not Found
        """
        response = client.get(
            f"/api/v1/time-entries/{soft_deleted_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_time_entry_description_length(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test description field requirements

        Contract specification:
        - Description should be at least 10 characters
        - Should be descriptive for billing/reporting purposes
        """
        response = client.get(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        description = entry_data["description"]
        assert len(description) >= 10  # Minimum meaningful description

    def test_get_time_entry_business_rules(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test business rule validations in response

        Contract specification:
        - Billable time should have meaningful descriptions
        - Hours should be reasonable (0 < hours <= 24)
        """
        response = client.get(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()

        # Business rule: reasonable hours
        assert 0 < entry_data["hours"] <= 24

        # Business rule: if billable, should have substantial description
        if entry_data["billable"]:
            assert len(entry_data["description"]) >= 10