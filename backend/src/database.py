"""
Database Connection and Session Management

Educational comparison between SQLAlchemy database configuration and
Spring Boot DataSource/JPA configuration patterns.

SQLAlchemy approach:
- Engine creation with connection pooling
- Sessionmaker factory for database sessions
- Dependency injection via FastAPI Depends
- Manual session lifecycle management

Spring Boot equivalent:
@Configuration
public class DatabaseConfig {
    @Bean
    public DataSource dataSource() {
        return DataSourceBuilder.create()
            .url("jdbc:postgresql://localhost/db")
            .build();
    }

    @Bean
    public EntityManagerFactory entityManagerFactory() {
        return new HibernateJpaVendorAdapter();
    }
}
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import get_settings

# Get application settings
settings = get_settings()

# Create database engine with connection pooling
# Similar to Spring Boot's DataSource configuration
engine = create_engine(
    settings.database_url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    echo=settings.database.echo,  # Log SQL queries
    pool_pre_ping=True,  # Validate connections before use
)

# Create sessionmaker factory
# Similar to Spring Boot's EntityManagerFactory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator:
    """
    Database session dependency for FastAPI.

    This function provides database sessions to FastAPI route handlers
    via dependency injection. Similar to Spring Boot's @Autowired
    EntityManager or Repository injection.

    Spring Boot equivalent:
    @Repository
    public class EmployeeRepository {
        @PersistenceContext
        private EntityManager entityManager;
    }

    Usage in FastAPI:
    @app.get("/employees")
    def get_employees(db: Session = Depends(get_db)):
        return db.query(Employee).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database health check utility
def check_database_health() -> bool:
    """
    Check database connectivity.

    Spring Boot equivalent:
    @Component
    public class DatabaseHealthIndicator implements HealthIndicator {
        @Override
        public Health health() {
            try {
                // Check database connection
                return Health.up().build();
            } catch (Exception e) {
                return Health.down(e).build();
            }
        }
    }
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception:
        return False


# Educational Notes: Database Session Management
#
# 1. Connection Pooling:
#    SQLAlchemy: Engine with pool_size and max_overflow
#    Spring Boot: HikariCP with spring.datasource.hikari.* properties
#
# 2. Session Lifecycle:
#    SQLAlchemy: Manual session creation/cleanup in dependency function
#    Spring Boot: @Transactional methods with automatic session management
#
# 3. Transaction Management:
#    SQLAlchemy: Explicit commit/rollback or context managers
#    Spring Boot: Declarative @Transactional annotations
#
# 4. Dependency Injection:
#    SQLAlchemy: FastAPI Depends() with generator functions
#    Spring Boot: @Autowired/@Inject with IoC container
#
# 5. Health Checks:
#    SQLAlchemy: Custom health check functions
#    Spring Boot: Actuator health indicators with auto-configuration
#
# 6. Configuration:
#    SQLAlchemy: Pydantic settings with environment variables
#    Spring Boot: application.yml with @ConfigurationProperties
#
# Both approaches provide:
# - Connection pooling and management
# - Transaction boundaries
# - Health monitoring
# - Environment-specific configuration