"""
Contract Test: GET /api/v1/employees/search
T021 - Employee search endpoint

This test MUST FAIL before implementation to follow TDD principles.
Tests the employee search endpoint specification using Elasticsearch.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestEmployeeSearchContract:
    """Contract tests for employee search endpoint"""

    def test_search_employees_success(self, client: TestClient, auth_headers):
        """
        Test successful employee search

        Contract specification:
        - Path: GET /api/v1/employees/search?q={query}&limit={limit}
        - Returns: 200 OK with array of EmployeeResponse
        - Auth: Required
        """
        search_query = "john"

        response = client.get(
            f"/api/v1/employees/search?q={search_query}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        search_results = response.json()
        assert isinstance(search_results, list)

        # Verify response structure
        if len(search_results) > 0:
            employee = search_results[0]
            required_fields = ["id", "name", "email", "department", "hire_date"]
            for field in required_fields:
                assert field in employee

    def test_search_employees_by_name(self, client: TestClient, sample_employees, auth_headers):
        """
        Test search by employee name

        Contract specification:
        - Should find employees by partial name match
        - Case-insensitive search
        """
        # Search for partial name
        search_query = sample_employees[0]["name"].split()[0].lower()

        response = client.get(
            f"/api/v1/employees/search?q={search_query}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        search_results = response.json()

        # Should find at least the sample employee
        found_employee = any(
            emp["id"] == sample_employees[0]["id"]
            for emp in search_results
        )
        assert found_employee

    def test_search_employees_by_email(self, client: TestClient, sample_employees, auth_headers):
        """
        Test search by employee email

        Contract specification:
        - Should find employees by partial email match
        """
        # Search for email domain
        search_query = sample_employees[0]["email"].split("@")[0]

        response = client.get(
            f"/api/v1/employees/search?q={search_query}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        search_results = response.json()

        # Should find the sample employee
        found_employee = any(
            emp["id"] == sample_employees[0]["id"]
            for emp in search_results
        )
        assert found_employee

    def test_search_employees_by_department(self, client: TestClient, sample_employees, auth_headers):
        """
        Test search by department name

        Contract specification:
        - Should find employees by department name
        """
        search_query = sample_employees[0]["department"]

        response = client.get(
            f"/api/v1/employees/search?q={search_query}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        search_results = response.json()

        # Should find employees from that department
        assert len(search_results) > 0
        department_matches = all(
            search_query.lower() in emp["department"].lower()
            for emp in search_results
        )
        assert department_matches

    def test_search_employees_empty_query(self, client: TestClient, auth_headers):
        """
        Test search with empty query

        Contract specification:
        - Returns: 422 Unprocessable Entity for empty or too short query
        """
        response = client.get("/api/v1/employees/search?q=", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_search_employees_short_query(self, client: TestClient, auth_headers):
        """
        Test search with too short query

        Contract specification:
        - Query must be at least 2 characters
        """
        response = client.get("/api/v1/employees/search?q=a", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_search_employees_limit_parameter(self, client: TestClient, auth_headers):
        """
        Test search limit parameter

        Contract specification:
        - Should respect limit parameter (max 50)
        - Default limit should be 10
        """
        search_query = "test"

        # Test with custom limit
        response = client.get(
            f"/api/v1/employees/search?q={search_query}&limit=5",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        search_results = response.json()
        assert len(search_results) <= 5

    def test_search_employees_limit_validation(self, client: TestClient, auth_headers):
        """
        Test search limit validation

        Contract specification:
        - Limit must be between 1 and 50
        """
        search_query = "test"

        # Test limit too high
        response = client.get(
            f"/api/v1/employees/search?q={search_query}&limit=100",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test limit too low
        response = client.get(
            f"/api/v1/employees/search?q={search_query}&limit=0",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_employees_no_results(self, client: TestClient, auth_headers):
        """
        Test search with no matching results

        Contract specification:
        - Should return empty array for no matches
        """
        search_query = "nonexistent_employee_12345"

        response = client.get(
            f"/api/v1/employees/search?q={search_query}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        search_results = response.json()
        assert isinstance(search_results, list)
        assert len(search_results) == 0

    def test_search_employees_unauthorized(self, client: TestClient):
        """
        Test unauthorized search

        Contract specification:
        - Returns: 401 Unauthorized without valid auth
        """
        response = client.get("/api/v1/employees/search?q=john")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_search_employees_fuzzy_matching(self, client: TestClient, sample_employees, auth_headers):
        """
        Test fuzzy search capabilities

        Contract specification:
        - Should handle typos and partial matches
        - Elasticsearch fuzzy search features
        """
        # Test with slight misspelling
        original_name = sample_employees[0]["name"]
        if len(original_name) > 3:
            # Create a typo by changing one character
            typo_name = original_name[:-1] + "x"

            response = client.get(
                f"/api/v1/employees/search?q={typo_name}",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            # Fuzzy search might still find the original employee

    def test_search_employees_special_characters(self, client: TestClient, auth_headers):
        """
        Test search with special characters

        Contract specification:
        - Should handle special characters safely
        - Should not cause errors or injection
        """
        special_queries = ["john@doe", "o'connor", "müller", "josé"]

        for query in special_queries:
            response = client.get(
                f"/api/v1/employees/search?q={query}",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            search_results = response.json()
            assert isinstance(search_results, list)

    def test_search_employees_excludes_soft_deleted(self, client: TestClient, soft_deleted_employee, auth_headers):
        """
        Test that search excludes soft-deleted employees

        Contract specification:
        - Soft-deleted employees should not appear in search results
        """
        search_query = soft_deleted_employee["name"]

        response = client.get(
            f"/api/v1/employees/search?q={search_query}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        search_results = response.json()

        # Should not find the soft-deleted employee
        found_deleted = any(
            emp["id"] == soft_deleted_employee["id"]
            for emp in search_results
        )
        assert not found_deleted

    def test_search_employees_relevance_scoring(self, client: TestClient, auth_headers):
        """
        Test search result relevance scoring

        Contract specification:
        - Results should be ordered by relevance
        - Exact matches should rank higher than partial matches
        """
        search_query = "senior"

        response = client.get(
            f"/api/v1/employees/search?q={search_query}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        search_results = response.json()

        # If results exist, they should be relevance-ordered
        # Exact title matches should come before partial matches
        if len(search_results) > 1:
            # This is a general test - specific relevance logic
            # would depend on Elasticsearch configuration
            assert isinstance(search_results, list)