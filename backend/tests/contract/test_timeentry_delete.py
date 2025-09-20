"""
Contract Test: DELETE /api/v1/time-entries/{id}
T026 - Time entry delete endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the time entry soft delete endpoint specification.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestTimeEntryDeleteContract:
    """Contract tests for time entry DELETE (soft delete) endpoint"""

    def test_delete_time_entry_success(self, client: TestClient, sample_time_entry, auth_headers):
        """
        Test successful time entry soft delete

        Contract specification:
        - Path: DELETE /api/v1/time-entries/{time_entry_id}
        - Returns: 204 No Content
        - Auth: Required
        - Behavior: Soft delete (preserves billing/audit data)
        """
        response = client.delete(
            f"/api/v1/time-entries/{sample_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""

        # Verify time entry is soft deleted by checking it's not in list
        list_response = client.get("/api/v1/time-entries/", headers=auth_headers)
        assert list_response.status_code == status.HTTP_200_OK

        data = list_response.json()
        entry_ids = [entry["id"] for entry in data["time_entries"]]
        assert sample_time_entry["id"] not in entry_ids

    def test_delete_time_entry_not_found(self, client: TestClient, auth_headers):
        """
        Test delete of non-existent time entry

        Contract specification:
        - Returns: 404 Not Found for non-existent time entry
        """
        fake_id = "12345678-1234-5678-9abc-123456789999"

        response = client.delete(f"/api/v1/time-entries/{fake_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "detail" in error_data

    def test_delete_time_entry_unauthorized(self, client: TestClient, sample_time_entry):
        """
        Test unauthorized delete

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        response = client.delete(f"/api/v1/time-entries/{sample_time_entry['id']}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_time_entry_invalid_uuid(self, client: TestClient, auth_headers):
        """
        Test delete with invalid UUID format

        Contract specification:
        - Returns: 422 Unprocessable Entity for invalid UUID
        """
        response = client.delete("/api/v1/time-entries/invalid-uuid", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_delete_time_entry_already_deleted(self, client: TestClient, soft_deleted_time_entry, auth_headers):
        """
        Test delete of already soft-deleted time entry

        Contract specification:
        - Returns: 404 Not Found for already deleted time entry
        """
        response = client.delete(
            f"/api/v1/time-entries/{soft_deleted_time_entry['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND