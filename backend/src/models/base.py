"""
Base SQLAlchemy Model Configuration

Educational comparison between SQLAlchemy declarative base and
JPA Entity base class patterns.

SQLAlchemy approach:
- Declarative base for all models
- Mixin classes for common fields
- UUID primary keys with automatic generation
- Timestamp tracking via mixins

JPA/Hibernate equivalent:
@MappedSuperclass
public abstract class BaseEntity {
    @Id
    @GeneratedValue
    private UUID id;

    @CreationTimestamp
    private LocalDateTime createdAt;

    @UpdateTimestamp
    private LocalDateTime updatedAt;
}
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


@as_declarative()
class Base:
    """
    Base class for all SQLAlchemy models.

    Similar to JPA's @MappedSuperclass, this provides common
    functionality for all entity classes.
    """

    id: Any
    __name__: str

    # Generate __tablename__ automatically
    # Similar to JPA's @Table annotation with automatic naming
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Auto-generate table name from class name.

        Converts CamelCase to snake_case:
        - Employee -> employees
        - TimeEntry -> time_entries
        """
        import re

        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
        return f"{name}s"  # Pluralize table names


class UUIDAuditMixin:
    """
    Mixin providing UUID primary key and audit timestamps.

    This pattern is similar to Spring Data JPA's @EntityListeners
    with AuditingEntityListener for automatic audit field management.

    JPA equivalent:
    @EntityListeners(AuditingEntityListener.class)
    public abstract class AuditableEntity {
        @Id
        @GeneratedValue
        private UUID id;

        @CreatedDate
        private LocalDateTime createdAt;

        @LastModifiedDate
        private LocalDateTime updatedAt;
    }
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key using UUID v4",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp",
    )

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Similar to Java's toString() method override in entity classes.
        """
        return f"<{self.__class__.__name__}(id={self.id})>"


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.

    Instead of physically deleting records, mark them as deleted.
    This preserves data integrity for historical reporting.

    JPA equivalent using @SQLDelete and @Where annotations:
    @SQLDelete(sql = "UPDATE employees SET deleted_at = NOW() WHERE id = ?")
    @Where(clause = "deleted_at IS NULL")
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Soft delete timestamp",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        if not self.is_deleted:
            self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore soft deleted record."""
        self.deleted_at = None


# Educational Notes: SQLAlchemy vs JPA Model Patterns
#
# 1. Inheritance Strategy:
#    SQLAlchemy: Mixins with multiple inheritance
#    JPA: @MappedSuperclass or @Inheritance strategies
#
# 2. Primary Key Generation:
#    SQLAlchemy: default=uuid.uuid4 in column definition
#    JPA: @GeneratedValue with UUID strategy
#
# 3. Audit Fields:
#    SQLAlchemy: server_default=func.now() with database triggers
#    JPA: @CreatedDate/@LastModifiedDate with @EnableJpaAuditing
#
# 4. Soft Delete:
#    SQLAlchemy: Manual implementation with custom queries
#    JPA: @SQLDelete/@Where annotations with Hibernate
#
# 5. Table Naming:
#    SQLAlchemy: @declared_attr with custom logic
#    JPA: @Table annotation or ImplicitNamingStrategy
#
# 6. Relationships:
#    SQLAlchemy: relationship() with back_populates
#    JPA: @OneToMany/@ManyToOne with mappedBy
#
# Both approaches provide:
# - Automatic timestamp management
# - UUID primary keys
# - Soft delete capabilities
# - Clean separation of concerns via mixins/inheritance