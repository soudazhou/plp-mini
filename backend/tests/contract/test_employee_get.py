"""
Contract Test: GET /api/v1/employees/{id}

This test suite defines the API contract for retrieving a single employee.
It MUST run (and currently fail) before the endpoint implementation exists
so that we maintain a TDD flow for the remaining CRUD operations.

Educational comparison between FastAPI's TestClient-driven contract
verification and Spring Boot's MockMvc approach to controller tests.

FastAPI pattern:
- Dependency overrides to inject an in-memory database
- pytest fixtures for arranging related entities
- Direct JSON assertions against the expected schema

Spring Boot equivalent:
@WebMvcTest(EmployeeController.class)
class EmployeeControllerGetContractTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    void shouldReturnEmployeeById() throws Exception {
        mockMvc.perform(get("/api/v1/employees/{id}", employeeId))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(employeeId))
            .andExpect(jsonPath("$.department").value("Corporate Law"));
    }
}
"""

import uuid

import pytest
from fastapi import status


class TestEmployeeGetContract:
    """Contract tests for GET /api/v1/employees/{id}."""

    @pytest.mark.contract
    def test_get_employee_success(self, client, sample_employee, auth_headers):
        """
        Contract: Successful retrieval returns a fully populated Employee payload.

        Expected behavior mirrors the OpenAPI employee schema: UUID identifier,
        core profile attributes, and audit timestamps. We assert these fields even
        though the endpoint is not yet implemented so future logic stays aligned
        with the contract-first design. Spring Boot MockMvc tests follow the same
        arrange-act-assert flow but rely on MockMvcResultMatchers for JSON paths.
        """
        response = client.get(
            f"/api/v1/employees/{sample_employee.id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        payload = response.json()
        assert payload["id"] == str(sample_employee.id)
        assert payload["name"] == sample_employee.name
        assert payload["email"] == sample_employee.email
        assert payload["department"] == sample_employee.department.name
        assert payload["hire_date"] == sample_employee.hire_date.isoformat()
        assert "created_at" in payload
        assert "updated_at" in payload

    @pytest.mark.contract
    def test_get_employee_not_found(self, client, auth_headers):
        """
        Contract: Unknown identifiers produce a 404 error payload.

        FastAPI surfaces HTTPException(status_code=404) similar to Spring's
        ResponseStatusException. We only assert the status code and presence of a
        JSON body so the implementation remains flexible while staying within the
        published contract.
        """
        missing_employee_id = uuid.uuid4()

        response = client.get(
            f"/api/v1/employees/{missing_employee_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_body = response.json()
        assert "detail" in error_body

    @pytest.mark.contract
    def test_get_employee_unauthorized(self, client, sample_employee):
        """
        Contract: Auth is required; missing credentials yield 401.

        Mirrors Spring Security's `@WithMockUser` tests where absence of
        authentication triggers `HttpStatus.UNAUTHORIZED`. Stubbing auth headers
        at the fixture layer keeps the contract test focused on I/O validation.
        """
        response = client.get(f"/api/v1/employees/{sample_employee.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
