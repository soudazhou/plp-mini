"""
Contract Test: PUT /api/v1/time-entries/{id}
T025 - Time entry update endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the time entry update endpoint specification.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestTimeEntryPutContract:
    """Contract tests for time entry PUT (update) endpoint"""

    def test_update_time_entry_success(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test successful time entry update

        Contract specification:
        - Path: PUT /api/v1/time-entries/{time_entry_id}
        - Body: TimeEntryUpdate (partial update allowed)
        - Returns: 200 OK with TimeEntryResponse
        - Auth: Required
        """
        update_data = {
            "hours": 6.5,
            "description": "Updated work description for client meeting",
            "billable": True
        }

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        assert entry_data["id"] == sample_time_entry["id"]
        assert entry_data["hours"] == update_data["hours"]
        assert entry_data["description"] == update_data["description"]
        assert entry_data["billable"] == update_data["billable"]
        assert "updated_at" in entry_data

    def test_update_time_entry_partial_update(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test partial time entry update (only hours)

        Contract specification:
        - Should allow partial updates (not all fields required)
        """
        update_data = {"hours": 4.0}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        assert entry_data["hours"] == update_data["hours"]
        assert entry_data["description"] == sample_time_entry["description"]  # Unchanged

    def test_update_time_entry_not_found(self, client: TestClient, auth_headers):
        """
        Test update of non-existent time entry

        Contract specification:
        - Returns: 404 Not Found for non-existent time entry
        """
        fake_id = "12345678-1234-5678-9abc-123456789999"
        update_data = {"hours": 5.0}

        response = client.put(
            f"/api/v1/time-entries/{fake_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "detail" in error_data

    def test_update_time_entry_invalid_hours(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test update with invalid hours

        Contract specification:
        - Hours must be > 0 and <= 24
        - Returns: 422 Unprocessable Entity for invalid hours
        """
        # Test negative hours
        update_data = {"hours": -1.0}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test hours > 24
        update_data = {"hours": 25.0}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_time_entry_invalid_description(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test update with invalid description

        Contract specification:
        - Description must be at least 10 characters for meaningful work tracking
        """
        update_data = {"description": "short"}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_update_time_entry_unauthorized(self, client: TestClient, sample_time_entry):
        """
        Test unauthorized update

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        update_data = {"hours": 5.0}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_time_entry_invalid_uuid(self, client: TestClient, auth_headers):
        """
        Test update with invalid UUID format

        Contract specification:
        - Returns: 422 Unprocessable Entity for invalid UUID
        """
        update_data = {"hours": 5.0}

        response = client.put(
            "/api/v1/time-entries/invalid-uuid",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_time_entry_date_change(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test updating time entry date

        Contract specification:
        - Should allow date change within reasonable bounds
        - Date cannot be in the future
        """
        from datetime import date, timedelta

        past_date = (date.today() - timedelta(days=7)).isoformat()
        update_data = {"date": past_date}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        assert entry_data["date"] == past_date

    def test_update_time_entry_future_date_forbidden(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test updating with future date

        Contract specification:
        - Date cannot be in the future
        """
        from datetime import date, timedelta

        future_date = (date.today() + timedelta(days=1)).isoformat()
        update_data = {"date": future_date}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_update_time_entry_employee_change(self, client: TestClient, sample_time_entry, sample_employee_2, auth_headers):
        """
        Test updating time entry employee assignment

        Contract specification:
        - Should allow employee reassignment with valid employee_id
        """
        update_data = {"employee_id": sample_employee_2["id"]}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        assert entry_data["employee"]["id"] == sample_employee_2["id"]

    def test_update_time_entry_invalid_employee(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test updating with non-existent employee

        Contract specification:
        - Returns: 400 Bad Request for invalid employee_id
        """
        fake_employee_id = "12345678-1234-5678-9abc-123456789999"
        update_data = {"employee_id": fake_employee_id}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "detail" in error_data

    def test_update_time_entry_billable_rules(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test billable time business rules

        Contract specification:
        - Billable time should have detailed description (>= 20 chars)
        """
        # Test billable with short description
        update_data = {
            "billable": True,
            "description": "short desc"
        }

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_time_entry_hours_precision(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test hours field precision

        Contract specification:
        - Should support decimal hours (e.g., 7.5, 1.25)
        """
        update_data = {"hours": 7.75}  # 7 hours 45 minutes

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        assert entry_data["hours"] == 7.75

    def test_update_time_entry_soft_deleted_not_found(self, client: TestClient, soft_deleted_time_entry, auth_headers):
        """
        Test that soft-deleted time entries cannot be updated

        Contract specification:
        - Soft-deleted time entries should return 404 Not Found
        """
        update_data = {"hours": 5.0}

        response = client.put(
            f"/api/v1/time-entries/{soft_deleted_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_time_entry_audit_trail(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test audit trail on update

        Contract specification:
        - updated_at should be set to current timestamp
        - created_at should remain unchanged
        """
        original_created_at = sample_time_entry["created_at"]
        update_data = {"hours": 6.0}

        response = client.put(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        entry_data = response.json()
        assert entry_data["created_at"] == original_created_at  # Unchanged
        assert "updated_at" in entry_data  # Should be updated