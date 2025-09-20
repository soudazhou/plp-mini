"""
Contract Test: GET /api/v1/time-entries
T023 - Time entry list endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the time entry list endpoint specification.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestTimeEntryListContract:
    """Contract tests for time entry list endpoint"""

    def test_list_time_entries_success(self, client: TestClient, auth_headers):
        """
        Test successful time entry list retrieval

        Contract specification:
        - Path: GET /api/v1/time-entries
        - Returns: 200 OK with TimeEntryListResponse
        - Auth: Required
        """
        response = client.get("/api/v1/time-entries/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "time_entries" in data
        assert "pagination" in data
        assert isinstance(data["time_entries"], list)
        assert isinstance(data["pagination"], dict)

    def test_list_time_entries_pagination(self, client: TestClient, auth_headers):
        """
        Test time entry list pagination

        Contract specification:
        - Should support page and limit parameters
        - Default page=1, limit=20
        """
        response = client.get("/api/v1/time-entries/?page=1&limit=10", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        pagination = data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "pages" in pagination

        assert pagination["page"] == 1
        assert pagination["limit"] == 10

    def test_list_time_entries_employee_filter(self, client: TestClient, sample_employee, auth_headers):
        """
        Test filtering time entries by employee

        Contract specification:
        - Should support employee_id filter parameter
        """
        response = client.get(
            f"/api/v1/time-entries/?employee_id={sample_employee['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        time_entries = data["time_entries"]

        # All returned entries should belong to the specified employee
        for entry in time_entries:
            assert entry["employee_id"] == sample_employee["id"]

    def test_list_time_entries_date_range_filter(self, client: TestClient, auth_headers):
        """
        Test filtering time entries by date range

        Contract specification:
        - Should support start_date and end_date filter parameters
        """
        from datetime import date, timedelta

        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/time-entries/?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        time_entries = data["time_entries"]

        # All entries should be within the date range
        for entry in time_entries:
            entry_date = entry["date"]
            assert start_date <= entry_date <= end_date

    def test_list_time_entries_billable_filter(self, client: TestClient, auth_headers):
        """
        Test filtering time entries by billable status

        Contract specification:
        - Should support billable filter parameter
        """
        response = client.get("/api/v1/time-entries/?billable=true", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        time_entries = data["time_entries"]

        # All returned entries should be billable
        for entry in time_entries:
            assert entry["billable"] is True

    def test_list_time_entries_department_filter(self, client: TestClient, sample_department, auth_headers):
        """
        Test filtering time entries by department

        Contract specification:
        - Should support department filter parameter
        """
        response = client.get(
            f"/api/v1/time-entries/?department={sample_department['name']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        time_entries = data["time_entries"]

        # All entries should belong to employees from the specified department
        for entry in time_entries:
            assert entry["employee"]["department"] == sample_department["name"]

    def test_list_time_entries_search(self, client: TestClient, auth_headers):
        """
        Test searching time entries by description

        Contract specification:
        - Should support search parameter for description text
        """
        search_term = "meeting"

        response = client.get(
            f"/api/v1/time-entries/?search={search_term}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        time_entries = data["time_entries"]

        # All entries should contain the search term in description
        for entry in time_entries:
            assert search_term.lower() in entry["description"].lower()

    def test_list_time_entries_unauthorized(self, client: TestClient):
        """
        Test unauthorized access

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        response = client.get("/api/v1/time-entries/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_time_entries_response_schema(self, client: TestClient, auth_headers):
        """
        Test response schema matches TimeEntryListResponse

        Contract specification:
        - Response must match TimeEntryListResponse Pydantic model
        """
        response = client.get("/api/v1/time-entries/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify top-level structure
        assert "time_entries" in data
        assert "pagination" in data

        # Verify time entry structure
        if len(data["time_entries"]) > 0:
            entry = data["time_entries"][0]
            required_fields = [
                "id", "date", "hours", "description", "billable",
                "employee", "created_at", "updated_at"
            ]
            for field in required_fields:
                assert field in entry

            # Verify employee sub-object
            assert "id" in entry["employee"]
            assert "name" in entry["employee"]
            assert "department" in entry["employee"]

    def test_list_time_entries_sorting(self, client: TestClient, auth_headers):
        """
        Test time entry list sorting

        Contract specification:
        - Should support sort_by parameter
        - Default sort should be by date descending (newest first)
        """
        response = client.get("/api/v1/time-entries/?sort_by=date", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        time_entries = data["time_entries"]

        # Verify entries are sorted by date (newest first)
        if len(time_entries) > 1:
            for i in range(len(time_entries) - 1):
                current_date = time_entries[i]["date"]
                next_date = time_entries[i + 1]["date"]
                assert current_date >= next_date

    def test_list_time_entries_includes_employee_info(self, client: TestClient, auth_headers):
        """
        Test that time entries include employee information

        Contract specification:
        - Should include employee name and department for user-friendliness
        """
        response = client.get("/api/v1/time-entries/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        time_entries = data["time_entries"]

        for entry in time_entries:
            assert "employee" in entry
            employee = entry["employee"]
            assert "name" in employee
            assert "department" in employee
            assert isinstance(employee["name"], str)
            assert isinstance(employee["department"], str)

    def test_list_time_entries_pagination_validation(self, client: TestClient, auth_headers):
        """
        Test pagination parameter validation

        Contract specification:
        - Page must be >= 1
        - Limit must be between 1 and 100
        """
        # Test invalid page
        response = client.get("/api/v1/time-entries/?page=0", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test invalid limit (too high)
        response = client.get("/api/v1/time-entries/?limit=200", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test invalid limit (too low)
        response = client.get("/api/v1/time-entries/?limit=0", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_time_entries_excludes_deleted(self, client: TestClient, soft_deleted_time_entry, auth_headers):
        """
        Test that soft-deleted time entries are excluded

        Contract specification:
        - Soft-deleted time entries should not appear in list
        """
        response = client.get("/api/v1/time-entries/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        time_entries = data["time_entries"]

        # Should not find the soft-deleted entry
        entry_ids = [entry["id"] for entry in time_entries]
        assert soft_deleted_time_entry["id"] not in entry_ids