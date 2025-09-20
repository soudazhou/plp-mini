"""
Contract Test: GET /api/v1/employees/{id}
T018 - Employee retrieve endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the individual employee retrieval endpoint specification.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestEmployeeGetContract:
    """Contract tests for employee GET by ID endpoint"""

    def test_get_employee_success(self, client: TestClient, sample_employee, auth_headers):
        """
        Test successful employee retrieval by ID

        Contract specification:
        - Path: GET /api/v1/employees/{employee_id}
        - Returns: 200 OK with EmployeeResponse
        - Auth: Required
        """
        response = client.get(
            f"/api/v1/employees/{sample_employee['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        employee_data = response.json()
        assert employee_data["id"] == sample_employee["id"]
        assert employee_data["name"] == sample_employee["name"]
        assert employee_data["email"] == sample_employee["email"]
        assert employee_data["department"] == sample_employee["department"]
        assert "hire_date" in employee_data
        assert "created_at" in employee_data
        assert "updated_at" in employee_data

    def test_get_employee_not_found(self, client: TestClient, auth_headers):
        """
        Test employee not found error

        Contract specification:
        - Returns: 404 Not Found for non-existent employee
        """
        fake_id = "12345678-1234-5678-9abc-123456789999"
        response = client.get(f"/api/v1/employees/{fake_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "detail" in error_data

    def test_get_employee_invalid_uuid(self, client: TestClient, auth_headers):
        """
        Test invalid UUID format error

        Contract specification:
        - Returns: 422 Unprocessable Entity for invalid UUID
        """
        response = client.get("/api/v1/employees/invalid-uuid", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_get_employee_unauthorized(self, client: TestClient, sample_employee):
        """
        Test unauthorized access

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        response = client.get(f"/api/v1/employees/{sample_employee['id']}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_employee_soft_deleted_not_found(self, client: TestClient, soft_deleted_employee, auth_headers):
        """
        Test that soft-deleted employees are not returned

        Contract specification:
        - Soft-deleted employees should return 404 Not Found
        """
        response = client.get(
            f"/api/v1/employees/{soft_deleted_employee['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_employee_response_schema(self, client: TestClient, sample_employee, auth_headers):
        """
        Test response schema matches EmployeeResponse

        Contract specification:
        - Response must match EmployeeResponse Pydantic model
        """
        response = client.get(
            f"/api/v1/employees/{sample_employee['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        employee_data = response.json()

        # Required fields from EmployeeResponse schema
        required_fields = ["id", "name", "email", "department", "hire_date", "created_at", "updated_at"]
        for field in required_fields:
            assert field in employee_data, f"Missing required field: {field}"

        # Field type validations
        assert isinstance(employee_data["name"], str)
        assert isinstance(employee_data["email"], str)
        assert isinstance(employee_data["department"], str)
        assert len(employee_data["name"]) >= 2
        assert "@" in employee_data["email"]

    def test_get_employee_includes_department_name(self, client: TestClient, sample_employee, auth_headers):
        """
        Test that employee response includes department name, not just ID

        Contract specification:
        - Response should include department name for user-friendliness
        """
        response = client.get(
            f"/api/v1/employees/{sample_employee['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        employee_data = response.json()
        assert "department" in employee_data
        assert isinstance(employee_data["department"], str)
        assert len(employee_data["department"]) > 0