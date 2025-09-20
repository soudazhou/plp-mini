"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

Educational Note: Alembic vs Flyway Migration Patterns
=====================================================

Alembic (Python/SQLAlchemy):
- Model-driven schema changes
- Automatic detection of differences
- Python migration scripts with upgrade/downgrade
- Type-safe operations via SQLAlchemy

Flyway (Java/Spring Boot):
- SQL-first migration approach
- Manual SQL script creation
- Version-based sequential execution
- Database-agnostic SQL (mostly)

Example equivalent Flyway migration:
-- V${up_revision.replace('_', '')}__${message.replace(' ', '_').lower()}.sql
-- ${message}
-- Created: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """
    Apply forward migration.

    Equivalent to Flyway's forward migration execution.
    All operations here should be reversible in downgrade().
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """
    Reverse migration changes.

    Note: Flyway requires paid version for rollback support.
    Alembic includes rollback functionality by default.
    """
    ${downgrades if downgrades else "pass"}