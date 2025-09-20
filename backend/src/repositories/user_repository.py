"""
User Repository Implementation
T043 - User repository for authentication and user management

Repository pattern for User model data access layer.
Provides abstraction over database operations for user entities.

Spring Boot equivalent:
public interface UserRepository extends JpaRepository<User, UUID> {
    Optional<User> findByUsername(String username);
    Optional<User> findByEmail(String email);
    List<User> findByRoleAndIsActiveTrue(UserRole role, Pageable pageable);
}
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from models.user import User, UserRole
from repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User entity operations

    Provides CRUD operations and user-specific queries.
    Follows the Repository pattern to abstract database access.
    """

    def __init__(self, db: Session):
        super().__init__(db, User)

    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find user by username

        Args:
            username: The username to search for

        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(
            and_(
                User.username == username,
                User.deleted_at.is_(None)  # Exclude soft deleted
            )
        ).first()

    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address

        Args:
            email: The email address to search for

        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(
            and_(
                User.email == email,
                User.deleted_at.is_(None)
            )
        ).first()

    def exists_by_username(self, username: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if username already exists

        Args:
            username: Username to check
            exclude_id: User ID to exclude from check (for updates)

        Returns:
            True if username exists, False otherwise
        """
        query = self.db.query(User).filter(
            and_(
                User.username == username,
                User.deleted_at.is_(None)
            )
        )

        if exclude_id:
            query = query.filter(User.id != exclude_id)

        return query.first() is not None

    def exists_by_email(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if email already exists

        Args:
            email: Email to check
            exclude_id: User ID to exclude from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        query = self.db.query(User).filter(
            and_(
                User.email == email,
                User.deleted_at.is_(None)
            )
        )

        if exclude_id:
            query = query.filter(User.id != exclude_id)

        return query.first() is not None

    def find_by_role(
        self,
        role: UserRole,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        """
        Find users by role

        Args:
            role: User role to filter by
            active_only: Whether to only return active users
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of users matching the role
        """
        query = self.db.query(User).filter(
            and_(
                User.role == role,
                User.deleted_at.is_(None)
            )
        )

        if active_only:
            query = query.filter(User.is_active == True)

        return query.offset(skip).limit(limit).all()

    def find_active_users(self, skip: int = 0, limit: int = 20) -> List[User]:
        """
        Find all active users

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of active users
        """
        return self.db.query(User).filter(
            and_(
                User.is_active == True,
                User.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()

    def search_users(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        """
        Search users by username, email, or full name

        Args:
            search_term: Term to search for
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of users matching the search term
        """
        search_pattern = f"%{search_term}%"

        return self.db.query(User).filter(
            and_(
                (
                    User.username.ilike(search_pattern) |
                    User.email.ilike(search_pattern)
                ),
                User.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()

    def count_by_role(self, role: UserRole, active_only: bool = True) -> int:
        """
        Count users by role

        Args:
            role: User role to count
            active_only: Whether to only count active users

        Returns:
            Number of users with the specified role
        """
        query = self.db.query(User).filter(
            and_(
                User.role == role,
                User.deleted_at.is_(None)
            )
        )

        if active_only:
            query = query.filter(User.is_active == True)

        return query.count()

    def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deactivate a user (business operation, not delete)

        Args:
            user_id: ID of user to deactivate

        Returns:
            Updated user if found, None otherwise
        """
        user = self.find_by_id(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
        return user

    def reactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Reactivate a user

        Args:
            user_id: ID of user to reactivate

        Returns:
            Updated user if found, None otherwise
        """
        user = self.find_by_id(user_id)
        if user:
            user.is_active = True
            self.db.commit()
            self.db.refresh(user)
        return user

    def find_admins(self) -> List[User]:
        """
        Find all admin users

        Returns:
            List of users with admin role
        """
        return self.find_by_role(UserRole.ADMIN, active_only=True)

    def update_last_login(self, user_id: UUID) -> Optional[User]:
        """
        Update user's last login timestamp

        Args:
            user_id: ID of user who logged in

        Returns:
            Updated user if found, None otherwise
        """
        from datetime import datetime

        user = self.find_by_id(user_id)
        if user:
            # Note: We'd need to add last_login field to User model
            # user.last_login = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user