"""
Pytest Configuration and Shared Fixtures

Educational comparison between pytest fixtures and Spring Boot test configuration.

pytest approach:
- conftest.py files for shared test configuration
- @pytest.fixture decorators for dependency injection
- Parametrized tests and test data factories
- Automatic fixture discovery and injection

Spring Boot equivalent:
@TestConfiguration
public class TestConfig {
    @Bean
    @Primary
    public TestDatabase testDatabase() {
        return new TestDatabase();
    }
}

@DataJpaTest
@Import(TestConfig.class)
public class EmployeeRepositoryTest {
    @Autowired
    private TestEntityManager entityManager;
}
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from models.base import Base
from settings import get_settings


@pytest.fixture(scope="session")
def settings():
    """
    Test settings configuration.

    Spring Boot equivalent:
    @TestPropertySource(properties = {
        "spring.datasource.url=jdbc:h2:mem:testdb",
        "spring.jpa.hibernate.ddl-auto=create-drop"
    })
    """
    # Override database URL for testing
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["ENVIRONMENT"] = "testing"
    return get_settings()


@pytest.fixture(scope="session")
def engine(settings):
    """
    Test database engine with in-memory SQLite.

    Spring Boot equivalent:
    @TestConfiguration
    public class TestDatabaseConfig {
        @Bean
        @Primary
        public DataSource testDataSource() {
            return new EmbeddedDatabaseBuilder()
                .setType(EmbeddedDatabaseType.H2)
                .build();
        }
    }
    """
    # Use in-memory SQLite for faster tests
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Cleanup
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Database session with automatic rollback after each test.

    Spring Boot equivalent:
    @DataJpaTest
    public class EmployeeServiceTest {
        @Autowired
        private TestEntityManager entityManager;
        // Automatic rollback after each test
    }
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI test client with dependency overrides.

    Spring Boot equivalent:
    @SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
    @AutoConfigureMockMvc
    public class EmployeeControllerTest {
        @Autowired
        private MockMvc mockMvc;
    }
    """
    # Import here to avoid circular imports
    from main import app  # This will be created later
    from database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_department(db_session):
    """
    Create a sample department for testing.

    Spring Boot equivalent:
    @TestConfiguration
    public class TestDataFactory {
        public Department createSampleDepartment() {
            Department dept = new Department("Corporate Law", "Test department");
            return departmentRepository.save(dept);
        }
    }
    """
    from models.department import Department

    department = Department(
        name="Corporate Law",
        description="Sample department for testing"
    )
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


@pytest.fixture
def sample_user(db_session):
    """
    Create a sample user for authentication testing.

    Spring Boot equivalent:
    @WithMockUser(username = "testuser", roles = {"LAWYER"})
    public void testSecuredEndpoint() {
        // Test method with mock user
    }
    """
    from models.user import User, UserRole

    user = User(
        username="testuser",
        email="test@example.com",
        role=UserRole.LAWYER,
        is_active=True
    )
    user.set_password("testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_employee(db_session, sample_department, sample_user):
    """
    Create a sample employee for testing.

    Demonstrates fixture dependencies - employee requires department and user.
    """
    from datetime import date
    from models.employee import Employee

    employee = Employee(
        name="John Doe",
        email="john.doe@example.com",
        hire_date=date(2023, 1, 1),
        department_id=sample_department.id
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    # Link user to employee
    sample_user.employee_id = employee.id
    db_session.commit()

    return employee


@pytest.fixture
def sample_time_entry(db_session, sample_employee):
    """
    Create a sample time entry for testing.
    """
    from datetime import date
    from decimal import Decimal
    from models.time_entry import TimeEntry

    time_entry = TimeEntry(
        employee_id=sample_employee.id,
        date=date.today(),
        hours=Decimal("8.00"),
        description="Sample work for testing purposes",
        billable=True,
        matter_code="TEST-001"
    )
    db_session.add(time_entry)
    db_session.commit()
    db_session.refresh(time_entry)
    return time_entry


@pytest.fixture
def auth_headers(sample_user):
    """
    Generate authentication headers for API testing.

    Spring Boot equivalent:
    @WithMockUser(username = "testuser", authorities = {"ROLE_LAWYER"})
    or manual JWT token creation in test setup
    """
    # Placeholder for JWT token generation
    # In real implementation, this would create a valid JWT token
    fake_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.fake.token"
    return {"Authorization": f"Bearer {fake_token}"}


@pytest.fixture(scope="session")
def event_loop():
    """
    Event loop for async tests.

    Required for pytest-asyncio with session-scoped fixtures.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test data factories
class TestDataFactory:
    """
    Factory class for creating test data.

    Spring Boot equivalent:
    @Component
    public class TestDataBuilder {
        public Employee.Builder employeeBuilder() {
            return Employee.builder()
                .name("Test Employee")
                .email("test@example.com");
        }
    }
    """

    @staticmethod
    def employee_data(department_id=None, **overrides):
        """Create employee test data."""
        from datetime import date

        default_data = {
            "name": "Test Employee",
            "email": "test.employee@example.com",
            "hire_date": date(2023, 1, 1).isoformat(),
            "department_id": str(department_id) if department_id else None,
        }
        default_data.update(overrides)
        return default_data

    @staticmethod
    def time_entry_data(employee_id=None, **overrides):
        """Create time entry test data."""
        from datetime import date

        default_data = {
            "employee_id": str(employee_id) if employee_id else None,
            "date": date.today().isoformat(),
            "hours": 8.00,
            "description": "Test work description for contract testing",
            "billable": True,
            "matter_code": "TEST-001",
        }
        default_data.update(overrides)
        return default_data


# Test markers
def pytest_configure(config):
    """
    Register custom pytest markers.

    Equivalent to Spring Boot's test slices:
    @DataJpaTest, @WebMvcTest, @JsonTest, etc.
    """
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "contract: mark test as contract test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "database: mark test as requiring database")


# Educational Notes: pytest vs Spring Boot Testing
#
# 1. Test Configuration:
#    pytest: conftest.py files with @pytest.fixture
#    Spring Boot: @TestConfiguration classes with @Bean methods
#
# 2. Dependency Injection:
#    pytest: Automatic fixture injection by parameter names
#    Spring Boot: @Autowired annotations and constructor injection
#
# 3. Database Testing:
#    pytest: Session-scoped engine, function-scoped transactions
#    Spring Boot: @DataJpaTest with automatic rollback
#
# 4. Test Slicing:
#    pytest: Custom markers and fixture scoping
#    Spring Boot: @WebMvcTest, @DataJpaTest, @JsonTest annotations
#
# 5. Mock Configuration:
#    pytest: pytest-mock and dependency overrides
#    Spring Boot: @MockBean and @SpyBean annotations
#
# 6. Test Data:
#    pytest: Factory functions and parametrized fixtures
#    Spring Boot: @TestDataBuilder and @Factory patterns
#
# Both frameworks provide:
# - Test isolation and cleanup
# - Dependency injection for tests
# - Database transaction management
# - HTTP client testing utilities