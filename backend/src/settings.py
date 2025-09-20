"""
Application Settings Configuration

Educational comparison between FastAPI settings management and
Spring Boot's application.yml configuration approach.

FastAPI/Pydantic approach:
- Type-safe configuration with validation
- Environment variable mapping with defaults
- Nested configuration objects
- Automatic documentation generation

Spring Boot equivalent:
@ConfigurationProperties(prefix = "app")
public class AppConfig {
    private String name;
    private String version;
    // getters/setters
}
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """
    Database configuration settings.

    Spring Boot equivalent:
    spring:
      datasource:
        url: ${DATABASE_URL}
        driver-class-name: org.postgresql.Driver
    """

    url: str = Field(
        default="sqlite:///./test.db",
        description="Database connection URL",
    )
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=30, description="Max overflow connections")

    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """
    Redis configuration for job queuing (SQS alternative).

    AWS SQS equivalent configuration:
    aws:
      sqs:
        queue-url: ${AWS_SQS_QUEUE_URL}
        region: ${AWS_REGION}
    """

    url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", description="Celery result backend"
    )

    class Config:
        env_prefix = "REDIS_"


class ElasticsearchSettings(BaseSettings):
    """
    Elasticsearch configuration.

    Spring Boot equivalent:
    spring:
      elasticsearch:
        uris: ${ELASTICSEARCH_URL}
        username: ${ES_USERNAME:}
        password: ${ES_PASSWORD:}
    """

    url: str = Field(
        default="http://localhost:9200", description="Elasticsearch cluster URL"
    )
    index_prefix: str = Field(
        default="legalanalytics", description="Index name prefix"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")

    class Config:
        env_prefix = "ELASTICSEARCH_"


class StorageSettings(BaseSettings):
    """
    File storage configuration (local or AWS S3).

    Local development vs AWS S3 configuration patterns.
    """

    use_local_storage: bool = Field(
        default=True, description="Use local storage instead of S3"
    )
    local_storage_path: str = Field(
        default="./storage", description="Local storage directory"
    )
    local_storage_base_url: str = Field(
        default="http://localhost:8000", description="Base URL for local files"
    )

    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    aws_region: str = Field(default="us-east-1")
    aws_s3_bucket: Optional[str] = Field(default=None)

    class Config:
        env_prefix = ""  # Mixed prefixes, handled individually


class EmailSettings(BaseSettings):
    """
    Email configuration (local SMTP or AWS SNS).

    Spring Boot equivalent:
    spring:
      mail:
        host: ${SMTP_HOST}
        port: ${SMTP_PORT}
        username: ${SMTP_USER}
        password: ${SMTP_PASSWORD}
    """

    smtp_host: str = Field(default="localhost", description="SMTP server host")
    smtp_port: int = Field(default=1025, description="SMTP server port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_tls: bool = Field(default=False, description="Use TLS encryption")
    smtp_ssl: bool = Field(default=False, description="Use SSL encryption")
    email_from: str = Field(
        default="noreply@legalanalytics.com", description="Default from address"
    )

    # AWS SNS Configuration
    aws_sns_topic_arn: Optional[str] = Field(default=None)

    class Config:
        env_prefix = ""


class SecuritySettings(BaseSettings):
    """
    Security and authentication configuration.

    Spring Security equivalent:
    spring:
      security:
        jwt:
          secret: ${JWT_SECRET}
          expiration: ${JWT_EXPIRATION:86400}
    """

    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    access_token_expire_minutes: int = Field(
        default=1440, description="JWT token expiration in minutes"
    )
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")

    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    class Config:
        env_prefix = ""


class CORSSettings(BaseSettings):
    """
    CORS configuration for frontend access.

    Spring Boot equivalent:
    @CrossOrigin(origins = {"http://localhost:4200"})
    or via WebMvcConfigurer.addCorsMappings()
    """

    origins: List[str] = Field(
        default=["http://localhost:4200", "http://localhost:3000"],
        description="Allowed CORS origins",
    )
    allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS requests"
    )
    allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    allow_headers: List[str] = Field(
        default=["*"], description="Allowed request headers"
    )

    @validator("origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_prefix = "CORS_"


class Settings(BaseSettings):
    """
    Main application settings.

    Combines all configuration sections similar to Spring Boot's
    hierarchical configuration structure.
    """

    # Application info
    app_name: str = Field(default="LegalAnalytics Mini", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", description="Environment name")

    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 path prefix")
    max_upload_size: int = Field(
        default=10 * 1024 * 1024, description="Max upload size in bytes (10MB)"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )

    # Nested settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    elasticsearch: ElasticsearchSettings = ElasticsearchSettings()
    storage: StorageSettings = StorageSettings()
    email: EmailSettings = EmailSettings()
    security: SecuritySettings = SecuritySettings()
    cors: CORSSettings = CORSSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """Get database URL for SQLAlchemy."""
        return self.database.url

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ["development", "dev", "local"]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() in ["production", "prod"]

    @property
    def local_storage_root(self) -> str:
        """Get local storage root directory."""
        return self.storage.local_storage_path

    @property
    def jwt_secret_key(self) -> str:
        """Get JWT secret key."""
        return self.security.secret_key


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Equivalent to Spring Boot's @ConfigurationProperties beans
    which are singletons by default.

    The @lru_cache decorator ensures we only load settings once,
    similar to Spring Boot's configuration property caching.
    """
    return Settings()


# Educational Notes:
#
# FastAPI/Pydantic Settings vs Spring Boot Configuration:
#
# 1. Type Safety:
#    - FastAPI: Pydantic models with runtime validation
#    - Spring Boot: Compile-time validation with IDE support
#
# 2. Environment Variables:
#    - FastAPI: Automatic mapping via pydantic-settings
#    - Spring Boot: @Value annotations or @ConfigurationProperties
#
# 3. Validation:
#    - FastAPI: Pydantic validators with custom rules
#    - Spring Boot: Bean Validation (@Valid, @NotNull, etc.)
#
# 4. Profiles:
#    - FastAPI: Custom logic based on environment variable
#    - Spring Boot: Native profile support (@Profile annotations)
#
# 5. Refreshable Configuration:
#    - FastAPI: Manual reload required
#    - Spring Boot: @RefreshScope with Spring Cloud Config
#
# Both approaches provide:
# - Externalized configuration
# - Environment-specific settings
# - Validation and documentation
# - Type-safe access to configuration values