"""
Contract Test: GET /api/v1/employees

This test validates the API contract for listing employees with
pagination, filtering, and search capabilities.
"""

import pytest
from fastapi import status


class TestEmployeeListContract:
    """Contract tests for GET /api/v1/employees endpoint."""

    @pytest.mark.contract
    def test_list_employees_success(self, client, sample_employee, auth_headers):
        """Test successful employee listing with pagination."""
        response = client.get(
            "/api/v1/employees",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify response schema
        data = response.json()
        assert "employees" in data
        assert "pagination" in data
        assert isinstance(data["employees"], list)

        # Verify pagination schema
        pagination = data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "pages" in pagination

    @pytest.mark.contract
    def test_list_employees_with_filters(self, client, sample_employee, auth_headers):
        """Test employee listing with department filter."""
        response = client.get(
            f"/api/v1/employees?department={sample_employee.department.name}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # All returned employees should be from the specified department
        for employee in data["employees"]:
            assert employee["department"] == sample_employee.department.name

    @pytest.mark.contract
    def test_list_employees_search(self, client, sample_employee, auth_headers):
        """Test employee search functionality."""
        response = client.get(
            f"/api/v1/employees?search={sample_employee.name.split()[0]}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Search results should contain the employee
        employee_names = [emp["name"] for emp in data["employees"]]
        assert any(sample_employee.name.split()[0] in name for name in employee_names)

    @pytest.mark.contract
    def test_list_employees_unauthorized(self, client):
        """Test unauthorized access returns 401."""
        response = client.get("/api/v1/employees")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED