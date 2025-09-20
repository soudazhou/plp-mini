"""
Contract Test: PUT /api/v1/employees/{id}
T019 - Employee update endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the employee update endpoint specification.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestEmployeePutContract:
    """Contract tests for employee PUT (update) endpoint"""

    def test_update_employee_success(self, client: TestClient, sample_employee, auth_headers):
        """
        Test successful employee update

        Contract specification:
        - Path: PUT /api/v1/employees/{employee_id}
        - Body: EmployeeUpdate (partial update allowed)
        - Returns: 200 OK with EmployeeResponse
        - Auth: Required
        """
        update_data = {
            "name": "Updated Employee Name",
            "email": "updated.email@lawfirm.com"
        }

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        employee_data = response.json()
        assert employee_data["id"] == sample_employee["id"]
        assert employee_data["name"] == update_data["name"]
        assert employee_data["email"] == update_data["email"]
        assert "updated_at" in employee_data

    def test_update_employee_partial_update(self, client: TestClient, sample_employee, auth_headers):
        """
        Test partial employee update (only name)

        Contract specification:
        - Should allow partial updates (not all fields required)
        """
        update_data = {"name": "Only Name Updated"}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        employee_data = response.json()
        assert employee_data["name"] == update_data["name"]
        assert employee_data["email"] == sample_employee["email"]  # Unchanged

    def test_update_employee_not_found(self, client: TestClient, auth_headers):
        """
        Test update of non-existent employee

        Contract specification:
        - Returns: 404 Not Found for non-existent employee
        """
        fake_id = "12345678-1234-5678-9abc-123456789999"
        update_data = {"name": "Does Not Exist"}

        response = client.put(
            f"/api/v1/employees/{fake_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "detail" in error_data

    def test_update_employee_invalid_email(self, client: TestClient, sample_employee, auth_headers):
        """
        Test update with invalid email format

        Contract specification:
        - Returns: 422 Unprocessable Entity for invalid email
        """
        update_data = {"email": "invalid-email-format"}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_update_employee_duplicate_email(self, client: TestClient, sample_employee, sample_employee_2, auth_headers):
        """
        Test update with email that already exists

        Contract specification:
        - Returns: 409 Conflict for duplicate email
        """
        update_data = {"email": sample_employee_2["email"]}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        error_data = response.json()
        assert "detail" in error_data
        assert "email" in str(error_data["detail"]).lower()

    def test_update_employee_unauthorized(self, client: TestClient, sample_employee):
        """
        Test unauthorized update

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        update_data = {"name": "Unauthorized Update"}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_employee_invalid_uuid(self, client: TestClient, auth_headers):
        """
        Test update with invalid UUID format

        Contract specification:
        - Returns: 422 Unprocessable Entity for invalid UUID
        """
        update_data = {"name": "Invalid UUID"}

        response = client.put(
            "/api/v1/employees/invalid-uuid",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_employee_department_change(self, client: TestClient, sample_employee, sample_department_2, auth_headers):
        """
        Test updating employee department

        Contract specification:
        - Should allow department change with valid department_id
        """
        update_data = {"department_id": sample_department_2["id"]}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        employee_data = response.json()
        assert employee_data["department"] == sample_department_2["name"]

    def test_update_employee_invalid_department(self, client: TestClient, sample_employee, auth_headers):
        """
        Test updating with non-existent department

        Contract specification:
        - Returns: 400 Bad Request for invalid department_id
        """
        fake_department_id = "12345678-1234-5678-9abc-123456789999"
        update_data = {"department_id": fake_department_id}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "detail" in error_data

    def test_update_employee_name_validation(self, client: TestClient, sample_employee, auth_headers):
        """
        Test name field validation

        Contract specification:
        - Name must be at least 2 characters, max 100 characters
        """
        # Test too short name
        update_data = {"name": "A"}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test too long name
        update_data = {"name": "A" * 101}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_employee_future_hire_date(self, client: TestClient, sample_employee, auth_headers):
        """
        Test updating with future hire date

        Contract specification:
        - Hire date cannot be in the future
        """
        from datetime import date, timedelta

        future_date = (date.today() + timedelta(days=30)).isoformat()
        update_data = {"hire_date": future_date}

        response = client.put(
            f"/api/v1/employees/{sample_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_update_employee_soft_deleted_not_found(self, client: TestClient, soft_deleted_employee, auth_headers):
        """
        Test that soft-deleted employees cannot be updated

        Contract specification:
        - Soft-deleted employees should return 404 Not Found
        """
        update_data = {"name": "Should Not Work"}

        response = client.put(
            f"/api/v1/employees/{soft_deleted_employee['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND