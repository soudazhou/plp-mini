"""Initial tables for legal analytics

Revision ID: 001
Revises:
Create Date: 2025-09-19 12:00:00.000000

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
-- V001__Initial_tables_for_legal_analytics.sql
-- Initial tables for legal analytics
-- Created: 2025-09-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Apply forward migration.

    Equivalent to Flyway's forward migration execution.
    All operations here should be reversible in downgrade().
    """
    # Create departments table
    op.create_table('departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Primary key using UUID v4'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='Department name (unique)'),
        sa.Column('description', sa.Text(), nullable=True, comment='Department description'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_departments_name'), 'departments', ['name'], unique=False)

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Primary key using UUID v4'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('username', sa.String(length=50), nullable=False, comment='Unique username for login'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='Email address (unique)'),
        sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='Bcrypt hashed password'),
        sa.Column('role', sa.String(length=20), nullable=False, comment='User role for access control'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Account status flag'),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Associated employee ID (optional)'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True, comment='Last successful login timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_employee_id'), 'users', ['employee_id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create employees table
    op.create_table('employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Primary key using UUID v4'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft delete timestamp'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Full name of the employee'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='Email address (unique)'),
        sa.Column('hire_date', sa.Date(), nullable=False, comment='Date of hire'),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Department foreign key'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_employees_department_id'), 'employees', ['department_id'], unique=False)
    op.create_index(op.f('ix_employees_email'), 'employees', ['email'], unique=False)
    op.create_index(op.f('ix_employees_hire_date'), 'employees', ['hire_date'], unique=False)
    op.create_index(op.f('ix_employees_name'), 'employees', ['name'], unique=False)

    # Create time_entries table
    op.create_table('time_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Primary key using UUID v4'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Employee who logged the time'),
        sa.Column('date', sa.Date(), nullable=False, comment='Date when work was performed'),
        sa.Column('hours', sa.Numeric(precision=5, scale=2), nullable=False, comment='Hours worked (decimal with 2-digit precision)'),
        sa.Column('description', sa.Text(), nullable=False, comment='Description of work performed'),
        sa.Column('billable', sa.Boolean(), nullable=False, comment='Whether time is billable to client'),
        sa.Column('matter_code', sa.String(length=20), nullable=True, comment='Matter or case code (optional)'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_time_entries_billable'), 'time_entries', ['billable'], unique=False)
    op.create_index(op.f('ix_time_entries_date'), 'time_entries', ['date'], unique=False)
    op.create_index(op.f('ix_time_entries_employee_id'), 'time_entries', ['employee_id'], unique=False)
    op.create_index(op.f('ix_time_entries_matter_code'), 'time_entries', ['matter_code'], unique=False)

    # Create composite indexes for common queries
    op.create_index('ix_time_entries_employee_date', 'time_entries', ['employee_id', 'date'])
    op.create_index('ix_time_entries_date_billable', 'time_entries', ['date', 'billable'])

    # Add foreign key constraint for user.employee_id -> employees.id
    # Note: This creates a circular reference that needs careful handling
    op.create_foreign_key(
        'fk_users_employee_id',
        'users', 'employees',
        ['employee_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """
    Reverse migration changes.

    Note: Flyway requires paid version for rollback support.
    Alembic includes rollback functionality by default.
    """
    # Drop foreign key constraints first
    op.drop_constraint('fk_users_employee_id', 'users', type_='foreignkey')

    # Drop tables in reverse order of creation
    op.drop_table('time_entries')
    op.drop_table('employees')
    op.drop_table('users')
    op.drop_table('departments')