"""
Base Repository Pattern Implementation

Generic repository with common CRUD operations that other repositories inherit.
Provides type-safe database operations with SQLAlchemy.

Spring Boot equivalent:
public interface BaseRepository<T, ID> extends JpaRepository<T, ID> {
    Optional<T> findByIdAndDeletedAtIsNull(ID id);
    List<T> findAllByDeletedAtIsNull(Pageable pageable);
    void softDelete(T entity);
}
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.base import Base, SoftDeleteMixin

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing common CRUD operations

    Generic repository pattern that handles:
    - Basic CRUD operations
    - Soft delete support
    - Type safety with generics
    - Common query patterns
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def create(self, obj: ModelType) -> ModelType:
        """
        Create a new entity

        Args:
            obj: Entity to create

        Returns:
            Created entity with generated ID and timestamps
        """
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def find_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Find entity by ID (excluding soft deleted)

        Args:
            id: Entity ID

        Returns:
            Entity if found, None otherwise
        """
        query = self.db.query(self.model).filter(self.model.id == id)

        # Add soft delete filter if model supports it
        if issubclass(self.model, SoftDeleteMixin):
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def find_all(self, skip: int = 0, limit: int = 20) -> List[ModelType]:
        """
        Find all entities with pagination (excluding soft deleted)

        Args:
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of entities
        """
        query = self.db.query(self.model)

        # Add soft delete filter if model supports it
        if issubclass(self.model, SoftDeleteMixin):
            query = query.filter(self.model.deleted_at.is_(None))

        return query.offset(skip).limit(limit).all()

    def update(self, id: UUID, update_data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update entity by ID

        Args:
            id: Entity ID
            update_data: Dictionary of fields to update

        Returns:
            Updated entity if found, None otherwise
        """
        entity = self.find_by_id(id)
        if not entity:
            return None

        # Update fields
        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        # Update timestamp if supported
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, id: UUID) -> bool:
        """
        Hard delete entity by ID

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        entity = self.find_by_id(id)
        if not entity:
            return False

        self.db.delete(entity)
        self.db.commit()
        return True

    def soft_delete(self, id: UUID) -> bool:
        """
        Soft delete entity by ID (if model supports it)

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found or not supported
        """
        if not issubclass(self.model, SoftDeleteMixin):
            return False

        entity = self.find_by_id(id)
        if not entity:
            return False

        entity.deleted_at = datetime.utcnow()
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.utcnow()

        self.db.commit()
        return True

    def count(self) -> int:
        """
        Count total entities (excluding soft deleted)

        Returns:
            Total count
        """
        query = self.db.query(self.model)

        # Add soft delete filter if model supports it
        if issubclass(self.model, SoftDeleteMixin):
            query = query.filter(self.model.deleted_at.is_(None))

        return query.count()

    def exists(self, id: UUID) -> bool:
        """
        Check if entity exists by ID

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        return self.find_by_id(id) is not None

    def bulk_create(self, entities: List[ModelType]) -> List[ModelType]:
        """
        Create multiple entities in bulk

        Args:
            entities: List of entities to create

        Returns:
            List of created entities
        """
        self.db.add_all(entities)
        self.db.commit()
        for entity in entities:
            self.db.refresh(entity)
        return entities

    def find_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """
        Find entity by specific field value

        Args:
            field_name: Name of the field
            value: Value to search for

        Returns:
            Entity if found, None otherwise
        """
        if not hasattr(self.model, field_name):
            return None

        field = getattr(self.model, field_name)
        query = self.db.query(self.model).filter(field == value)

        # Add soft delete filter if model supports it
        if issubclass(self.model, SoftDeleteMixin):
            query = query.filter(self.model.deleted_at.is_(None))

        return query.first()

    def find_all_by_field(
        self,
        field_name: str,
        value: Any,
        skip: int = 0,
        limit: int = 20
    ) -> List[ModelType]:
        """
        Find all entities by specific field value

        Args:
            field_name: Name of the field
            value: Value to search for
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of entities
        """
        if not hasattr(self.model, field_name):
            return []

        field = getattr(self.model, field_name)
        query = self.db.query(self.model).filter(field == value)

        # Add soft delete filter if model supports it
        if issubclass(self.model, SoftDeleteMixin):
            query = query.filter(self.model.deleted_at.is_(None))

        return query.offset(skip).limit(limit).all()

    def refresh(self, entity: ModelType) -> ModelType:
        """
        Refresh entity from database

        Args:
            entity: Entity to refresh

        Returns:
            Refreshed entity
        """
        self.db.refresh(entity)
        return entity