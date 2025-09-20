"""
Alembic Environment Configuration for LegalAnalytics Mini

This file configures Alembic for database migrations with educational
comparisons to Java/Spring Boot Flyway migration patterns.

Java/Spring Boot Equivalent:
- application.yml: spring.flyway configuration
- V1__Create_tables.sql: Flyway versioned migrations
- FlywayMigrationStrategy: Custom migration strategies
"""

import logging
from logging.config import fileConfig
from typing import Any

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add the src directory to the path so we can import our models
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir / "src"))

# Import all models to ensure they're registered with SQLAlchemy
# Similar to @Entity scanning in Spring Boot JPA
from models.base import Base  # noqa: E402
from models.department import Department  # noqa: E402
from models.user import User  # noqa: E402
from models.employee import Employee  # noqa: E402
from models.time_entry import TimeEntry  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger(__name__)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url() -> str:
    """
    Get database URL with fallback to environment variable.

    Similar to Spring Boot's DataSource configuration:
    spring.datasource.url=${DATABASE_URL:jdbc:postgresql://localhost/legalanalytics}
    """
    import os

    # Try environment variable first (for Docker/production)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Fallback to alembic.ini configuration
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    Similar to Flyway's validate command - checks migrations without DB connection.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    logger.info("Running offline migrations...")
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Similar to Spring Boot's automatic Flyway migration on startup:
    spring.flyway.migrate-at-start=true
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    logger.info("Running online migrations...")
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect default value changes
            # Include schemas if using multiple schemas
            # include_schemas=True,
        )

        with context.begin_transaction():
            # Log migration context for debugging
            logger.info(f"Target metadata tables: {list(target_metadata.tables.keys())}")
            context.run_migrations()


# Educational Note: Migration Strategy Comparison
#
# Alembic (Python):
# - Declarative model definitions drive schema
# - Autogenerate compares models to database
# - Python-based migration scripts
# - Rollback supported via downgrade() functions
#
# Flyway (Java):
# - SQL-based versioned migrations
# - Sequential version numbering (V1, V2, etc.)
# - Java-based custom migrations via MigrationCallback
# - Limited rollback support (paid feature)
#
# Both approaches:
# - Version control for database schema
# - Repeatable, automated deployments
# - Schema validation and conflict detection
# - Integration with application frameworks

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()