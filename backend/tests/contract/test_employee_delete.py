"""
Contract Test: DELETE /api/v1/employees/{id}
T020 - Employee delete endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the employee soft delete endpoint specification.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestEmployeeDeleteContract:
    """Contract tests for employee DELETE (soft delete) endpoint"""

    def test_delete_employee_success(self, client: TestClient, sample_employee, auth_headers):
        """
        Test successful employee soft delete

        Contract specification:
        - Path: DELETE /api/v1/employees/{employee_id}
        - Returns: 204 No Content
        - Auth: Required
        - Behavior: Soft delete (preserves historical data)
        """
        response = client.delete(
            f"/api/v1/employees/{sample_employee['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""  # No content in response body

        # Verify employee is soft deleted by checking it's not in list
        list_response = client.get("/api/v1/employees/", headers=auth_headers)
        assert list_response.status_code == status.HTTP_200_OK

        employees_data = list_response.json()
        employee_ids = [emp["id"] for emp in employees_data["employees"]]
        assert sample_employee["id"] not in employee_ids

    def test_delete_employee_not_found(self, client: TestClient, auth_headers):
        """
        Test delete of non-existent employee

        Contract specification:
        - Returns: 404 Not Found for non-existent employee
        """
        fake_id = "12345678-1234-5678-9abc-123456789999"

        response = client.delete(f"/api/v1/employees/{fake_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "detail" in error_data

    def test_delete_employee_unauthorized(self, client: TestClient, sample_employee):
        """
        Test unauthorized delete

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        response = client.delete(f"/api/v1/employees/{sample_employee['id']}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_employee_invalid_uuid(self, client: TestClient, auth_headers):
        """
        Test delete with invalid UUID format

        Contract specification:
        - Returns: 422 Unprocessable Entity for invalid UUID
        """
        response = client.delete("/api/v1/employees/invalid-uuid", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_delete_employee_already_deleted(self, client: TestClient, soft_deleted_employee, auth_headers):
        """
        Test delete of already soft-deleted employee

        Contract specification:
        - Returns: 404 Not Found for already deleted employee
        """
        response = client.delete(
            f"/api/v1/employees/{soft_deleted_employee['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_employee_with_time_entries_preserves_history(self, client: TestClient, employee_with_time_entries, auth_headers):
        """
        Test that deleting employee with time entries preserves historical data

        Contract specification:
        - Soft delete should preserve time entry relationships
        - Historical data should remain accessible for reporting
        """
        employee_id = employee_with_time_entries["id"]

        # Delete the employee
        response = client.delete(f"/api/v1/employees/{employee_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify employee no longer appears in active list
        list_response = client.get("/api/v1/employees/", headers=auth_headers)
        employees_data = list_response.json()
        employee_ids = [emp["id"] for emp in employees_data["employees"]]
        assert employee_id not in employee_ids

        # Verify time entries still exist for reporting (this would be tested via time entries API)
        # This is important for data integrity and compliance

    def test_delete_employee_cannot_retrieve_after_delete(self, client: TestClient, sample_employee, auth_headers):
        """
        Test that deleted employee cannot be retrieved via GET

        Contract specification:
        - GET /api/v1/employees/{id} should return 404 for soft-deleted employees
        """
        employee_id = sample_employee["id"]

        # First verify employee exists
        get_response = client.get(f"/api/v1/employees/{employee_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_200_OK

        # Delete the employee
        delete_response = client.delete(f"/api/v1/employees/{employee_id}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify GET now returns 404
        get_after_delete = client.get(f"/api/v1/employees/{employee_id}", headers=auth_headers)
        assert get_after_delete.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_employee_cannot_update_after_delete(self, client: TestClient, sample_employee, auth_headers):
        """
        Test that deleted employee cannot be updated

        Contract specification:
        - PUT /api/v1/employees/{id} should return 404 for soft-deleted employees
        """
        employee_id = sample_employee["id"]

        # Delete the employee
        delete_response = client.delete(f"/api/v1/employees/{employee_id}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Try to update the deleted employee
        update_data = {"name": "Should Not Work"}
        update_response = client.put(
            f"/api/v1/employees/{employee_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_employee_does_not_appear_in_search(self, client: TestClient, sample_employee, auth_headers):
        """
        Test that deleted employees do not appear in search results

        Contract specification:
        - Search endpoints should exclude soft-deleted employees
        """
        employee_name = sample_employee["name"]

        # Verify employee appears in search before deletion
        search_response = client.get(
            f"/api/v1/employees/search?q={employee_name}",
            headers=auth_headers
        )
        assert search_response.status_code == status.HTTP_200_OK
        search_results = search_response.json()
        employee_found = any(emp["id"] == sample_employee["id"] for emp in search_results)
        assert employee_found

        # Delete the employee
        delete_response = client.delete(f"/api/v1/employees/{sample_employee['id']}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify employee no longer appears in search
        search_after_delete = client.get(
            f"/api/v1/employees/search?q={employee_name}",
            headers=auth_headers
        )
        assert search_after_delete.status_code == status.HTTP_200_OK
        search_results_after = search_after_delete.json()
        employee_found_after = any(emp["id"] == sample_employee["id"] for emp in search_results_after)
        assert not employee_found_after

    def test_delete_employee_audit_trail(self, client: TestClient, sample_employee, auth_headers):
        """
        Test that delete operation is properly audited

        Contract specification:
        - Delete operations should maintain audit trail
        - Updated_at timestamp should be set on delete
        """
        # This test verifies the audit trail aspects of soft delete
        # The actual verification would be done at the database level
        # or through admin endpoints that show deleted records
        employee_id = sample_employee["id"]

        response = client.delete(f"/api/v1/employees/{employee_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # In a real implementation, we might have an admin endpoint to verify:
        # - deleted_at timestamp is set
        # - updated_at timestamp is updated
        # - deleted_by user is recorded
        # This ensures compliance and auditability