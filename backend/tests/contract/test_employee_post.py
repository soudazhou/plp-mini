"""
Contract Test: POST /api/v1/employees

This test validates the API contract for creating new employees.
It MUST FAIL until the actual API endpoint is implemented.

Educational comparison between FastAPI contract testing and
Spring Boot MockMvc integration testing patterns.

pytest approach:
- TestClient for HTTP endpoint testing
- Fixtures for test data setup and cleanup
- Parametrized tests for multiple scenarios
- JSON schema validation

Spring Boot equivalent:
@WebMvcTest(EmployeeController.class)
public class EmployeeControllerContractTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    public void shouldCreateEmployee() throws Exception {
        mockMvc.perform(post("/api/v1/employees")
            .contentType(MediaType.APPLICATION_JSON)
            .content(employeeJson))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").exists());
    }
}
"""

import pytest
from fastapi import status


class TestEmployeePostContract:
    """
    Contract tests for POST /api/v1/employees endpoint.

    These tests define the expected behavior of the employee creation API
    based on the OpenAPI specification in contracts/employee-api.yaml.
    """

    @pytest.mark.contract
    def test_create_employee_success(self, client, sample_department, auth_headers):
        """
        Test successful employee creation.

        Contract: POST /api/v1/employees
        Expected: 201 Created with employee object
        Schema: EmployeeCreate -> Employee

        Spring Boot equivalent:
        @Test
        public void shouldCreateEmployeeWithValidData() {
            // Given valid employee data
            // When POST to /employees
            // Then return 201 with employee object
        }
        """
        from tests.conftest import TestDataFactory

        # Prepare request data according to EmployeeCreate schema
        employee_data = TestDataFactory.employee_data(
            department_id=sample_department.id,
            name="Jane Smith",
            email="jane.smith@lawfirm.com",
            hire_date="2023-02-01"
        )

        # Execute POST request
        response = client.post(
            "/api/v1/employees",
            json=employee_data,
            headers=auth_headers
        )

        # Verify response contract
        assert response.status_code == status.HTTP_201_CREATED

        # Verify response schema matches Employee model
        response_data = response.json()
        assert "id" in response_data
        assert response_data["name"] == employee_data["name"]
        assert response_data["email"] == employee_data["email"]
        assert response_data["hire_date"] == employee_data["hire_date"]
        assert response_data["department"] == sample_department.name
        assert "created_at" in response_data
        assert "updated_at" in response_data

        # Verify UUID format for ID
        import uuid
        assert uuid.UUID(response_data["id"])  # Should not raise exception

    @pytest.mark.contract
    def test_create_employee_validation_errors(self, client, sample_department, auth_headers):
        """
        Test validation error responses.

        Contract: POST /api/v1/employees with invalid data
        Expected: 400 Bad Request with ValidationError schema
        """
        test_cases = [
            # Missing required fields
            {
                "data": {},
                "expected_errors": ["name", "email", "department_id", "hire_date"]
            },
            # Invalid email format
            {
                "data": {
                    "name": "Test User",
                    "email": "invalid-email",
                    "department_id": str(sample_department.id),
                    "hire_date": "2023-01-01"
                },
                "expected_errors": ["email"]
            },
            # Name too short
            {
                "data": {
                    "name": "A",  # Less than 2 characters
                    "email": "test@example.com",
                    "department_id": str(sample_department.id),
                    "hire_date": "2023-01-01"
                },
                "expected_errors": ["name"]
            },
            # Future hire date
            {
                "data": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "department_id": str(sample_department.id),
                    "hire_date": "2030-01-01"  # Future date
                },
                "expected_errors": ["hire_date"]
            },
            # Invalid department ID format
            {
                "data": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "department_id": "invalid-uuid",
                    "hire_date": "2023-01-01"
                },
                "expected_errors": ["department_id"]
            }
        ]

        for test_case in test_cases:
            response = client.post(
                "/api/v1/employees",
                json=test_case["data"],
                headers=auth_headers
            )

            # Verify validation error response
            assert response.status_code == status.HTTP_400_BAD_REQUEST

            # Verify ValidationError schema
            error_data = response.json()
            assert "error" in error_data
            assert "code" in error_data
            assert error_data["code"] == "VALIDATION_ERROR"
            assert "details" in error_data
            assert isinstance(error_data["details"], list)
            assert "timestamp" in error_data

            # Verify specific field errors
            error_fields = [detail["field"] for detail in error_data["details"]]
            for expected_field in test_case["expected_errors"]:
                assert expected_field in error_fields

    @pytest.mark.contract
    def test_create_employee_duplicate_email(self, client, sample_department, sample_employee, auth_headers):
        """
        Test duplicate email conflict.

        Contract: POST /api/v1/employees with existing email
        Expected: 409 Conflict with Error schema
        """
        from tests.conftest import TestDataFactory

        # Try to create employee with existing email
        employee_data = TestDataFactory.employee_data(
            department_id=sample_department.id,
            email=sample_employee.email  # Use existing email
        )

        response = client.post(
            "/api/v1/employees",
            json=employee_data,
            headers=auth_headers
        )

        # Verify conflict response
        assert response.status_code == status.HTTP_409_CONFLICT

        # Verify Error schema
        error_data = response.json()
        assert "error" in error_data
        assert "code" in error_data
        assert error_data["code"] == "EMAIL_ALREADY_EXISTS"
        assert "timestamp" in error_data
        assert "email" in error_data["error"].lower()

    @pytest.mark.contract
    def test_create_employee_unauthorized(self, client, sample_department):
        """
        Test unauthorized access.

        Contract: POST /api/v1/employees without authentication
        Expected: 401 Unauthorized with Error schema
        """
        from tests.conftest import TestDataFactory

        employee_data = TestDataFactory.employee_data(department_id=sample_department.id)

        # Request without auth headers
        response = client.post(
            "/api/v1/employees",
            json=employee_data
        )

        # Verify unauthorized response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify Error schema
        error_data = response.json()
        assert "error" in error_data
        assert "code" in error_data
        assert "timestamp" in error_data

    @pytest.mark.contract
    def test_create_employee_nonexistent_department(self, client, auth_headers):
        """
        Test creation with non-existent department.

        Contract: POST /api/v1/employees with invalid department_id
        Expected: 400 Bad Request (foreign key constraint)
        """
        import uuid
        from tests.conftest import TestDataFactory

        # Use random UUID for non-existent department
        fake_department_id = uuid.uuid4()
        employee_data = TestDataFactory.employee_data(department_id=fake_department_id)

        response = client.post(
            "/api/v1/employees",
            json=employee_data,
            headers=auth_headers
        )

        # Verify bad request response
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Verify error mentions department
        error_data = response.json()
        assert "department" in error_data["error"].lower()

    @pytest.mark.contract
    def test_create_employee_content_type_validation(self, client, auth_headers):
        """
        Test Content-Type header validation.

        Contract: POST /api/v1/employees requires application/json
        Expected: 422 Unprocessable Entity for wrong content type
        """
        # Send form data instead of JSON
        response = client.post(
            "/api/v1/employees",
            data="name=Test&email=test@example.com",  # Form data
            headers={"Content-Type": "application/x-www-form-urlencoded", **auth_headers}
        )

        # Verify unprocessable entity response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.contract
    @pytest.mark.parametrize("role", ["HR_ADMIN", "PARTNER"])
    def test_create_employee_authorized_roles(self, client, sample_department, auth_headers, role):
        """
        Test that authorized roles can create employees.

        Contract: Only HR_ADMIN and PARTNER roles can create employees
        Expected: 201 Created for authorized roles

        Spring Boot equivalent:
        @Test
        @WithMockUser(authorities = {"ROLE_HR_ADMIN"})
        public void hrAdminCanCreateEmployee() {
            // Test HR admin access
        }
        """
        from tests.conftest import TestDataFactory

        # Modify auth headers to simulate different roles
        # In real implementation, this would use proper JWT tokens
        role_headers = {**auth_headers, "X-User-Role": role}

        employee_data = TestDataFactory.employee_data(department_id=sample_department.id)

        response = client.post(
            "/api/v1/employees",
            json=employee_data,
            headers=role_headers
        )

        # Should succeed for authorized roles
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.contract
    def test_create_employee_forbidden_role(self, client, sample_department, auth_headers):
        """
        Test that LAWYER role cannot create employees.

        Contract: LAWYER role should not have employee creation permission
        Expected: 403 Forbidden
        """
        from tests.conftest import TestDataFactory

        # Simulate LAWYER role
        lawyer_headers = {**auth_headers, "X-User-Role": "LAWYER"}

        employee_data = TestDataFactory.employee_data(department_id=sample_department.id)

        response = client.post(
            "/api/v1/employees",
            json=employee_data,
            headers=lawyer_headers
        )

        # Should be forbidden for LAWYER role
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Verify Error schema
        error_data = response.json()
        assert "error" in error_data
        assert "code" in error_data
        assert error_data["code"] == "INSUFFICIENT_PERMISSIONS"


# Educational Notes: Contract Testing Patterns
#
# 1. Test Structure:
#    pytest: Class-based test organization with descriptive method names
#    Spring Boot: Similar structure with @Test annotations
#
# 2. HTTP Testing:
#    pytest: TestClient with direct endpoint calls
#    Spring Boot: MockMvc with request builders and result matchers
#
# 3. Schema Validation:
#    pytest: Manual JSON structure assertions
#    Spring Boot: @JsonTest or manual ObjectMapper validation
#
# 4. Error Scenarios:
#    pytest: Parametrized tests for multiple error cases
#    Spring Boot: Multiple @Test methods or @ParameterizedTest
#
# 5. Authentication Testing:
#    pytest: Header-based simulation
#    Spring Boot: @WithMockUser or MockMvc security context
#
# 6. Contract-First Development:
#    - Tests define expected API behavior before implementation
#    - OpenAPI schema drives test expectations
#    - Failing tests guide implementation requirements
#    - Ensures API contract compliance
#
# Both approaches ensure:
# - API contract adherence
# - Proper error handling
# - Security requirement validation
# - Response schema compliance