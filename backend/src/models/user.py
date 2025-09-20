"""
User Model

Represents system authentication and authorization information.
This handles login credentials and role-based access control.

Educational comparison between SQLAlchemy authentication models and
Spring Security User entity patterns.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDAuditMixin


class UserRole(str, Enum):
    """
    User role enumeration for role-based access control.

    Spring Security equivalent:
    public enum Role {
        HR_ADMIN("ROLE_HR_ADMIN"),
        LAWYER("ROLE_LAWYER"),
        PARTNER("ROLE_PARTNER");

        private final String authority;
    }
    """

    HR_ADMIN = "HR_ADMIN"
    LAWYER = "LAWYER"
    PARTNER = "PARTNER"

    @classmethod
    def get_hierarchy(cls) -> dict[str, int]:
        """
        Role hierarchy for permission checking.

        Spring Security equivalent:
        @Bean
        public RoleHierarchy roleHierarchy() {
            RoleHierarchyImpl hierarchy = new RoleHierarchyImpl();
            hierarchy.setHierarchy("ROLE_PARTNER > ROLE_HR_ADMIN > ROLE_LAWYER");
            return hierarchy;
        }
        """
        return {
            cls.PARTNER: 3,  # Highest privileges
            cls.HR_ADMIN: 2,  # Administrative privileges
            cls.LAWYER: 1,  # Basic user privileges
        }

    def has_permission(self, required_role: "UserRole") -> bool:
        """Check if this role has permission for required role."""
        hierarchy = self.get_hierarchy()
        return hierarchy.get(self, 0) >= hierarchy.get(required_role, 0)


class User(Base, UUIDAuditMixin):
    """
    User entity for authentication and authorization.

    Spring Security equivalent:
    @Entity
    @Table(name = "users")
    public class User extends AuditableEntity implements UserDetails {
        @Column(unique = true, nullable = false)
        private String username;

        @Column(unique = true, nullable = false)
        private String email;

        @Column(nullable = false)
        private String password;

        @Enumerated(EnumType.STRING)
        private Role role;

        @OneToOne(mappedBy = "user")
        private Employee employee;
    }
    """

    __tablename__ = "users"

    # Authentication fields
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique username for login",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Email address (unique)",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password",
    )

    # Authorization fields
    role: Mapped[UserRole] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.LAWYER,
        comment="User role for access control",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Account status flag",
    )

    # Optional employee relationship
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Associated employee ID (optional)",
    )

    # Audit fields
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp",
    )

    # Relationships
    # employee: Mapped[Optional["Employee"]] = relationship(
    #     "Employee",
    #     back_populates="user",
    #     lazy="select",
    #     uselist=False,  # One-to-one relationship
    # )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        In production, this would use bcrypt or similar:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, self.hashed_password)

        Spring Security equivalent:
        @Autowired
        private PasswordEncoder passwordEncoder;

        public boolean checkPassword(String rawPassword) {
            return passwordEncoder.matches(rawPassword, this.password);
        }
        """
        # Placeholder - actual implementation would use bcrypt
        # This is just for educational purposes
        return password == "dummy_check"

    def set_password(self, password: str) -> None:
        """
        Hash and store password.

        Production implementation:
        self.hashed_password = pwd_context.hash(password)
        """
        # Placeholder - actual implementation would use bcrypt
        self.hashed_password = f"hashed_{password}"

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role."""
        return self.role == role

    def has_permission(self, required_role: UserRole) -> bool:
        """
        Check if user has permission based on role hierarchy.

        Spring Security equivalent:
        @PreAuthorize("hasRole('PARTNER') or hasRole('HR_ADMIN')")
        public void someMethod() { }
        """
        return self.role.has_permission(required_role)

    @property
    def is_admin(self) -> bool:
        """Check if user has administrative privileges."""
        return self.role in [UserRole.HR_ADMIN, UserRole.PARTNER]

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        if self.employee:
            return self.employee.name
        return self.username


# Educational Notes: User Model vs Spring Security
#
# 1. Authentication vs Authorization:
#    - Authentication: username/password verification
#    - Authorization: role-based access control
#    - Spring Security separates these concerns clearly
#
# 2. Password Security:
#    SQLAlchemy: Manual bcrypt integration
#    Spring Security: Built-in PasswordEncoder beans
#
# 3. Role Hierarchy:
#    SQLAlchemy: Custom enum with hierarchy logic
#    Spring Security: RoleHierarchy bean configuration
#
# 4. User Details:
#    SQLAlchemy: Custom User model with business logic
#    Spring Security: UserDetails interface implementation
#
# 5. Session Management:
#    SQLAlchemy: Manual last_login tracking
#    Spring Security: Built-in session management
#
# 6. Method Security:
#    SQLAlchemy: Custom has_permission() methods
#    Spring Security: @PreAuthorize/@Secured annotations
#
# Both approaches provide:
# - User authentication and authorization
# - Role-based access control
# - Password security best practices
# - Extensible permission systems