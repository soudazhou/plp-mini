"""
User Service with Authentication
T047 - User service with authentication

Provides user management and authentication functionality including
login, logout, password management, and session handling.

Spring Boot equivalent:
@Service
@Transactional
public class UserService {
    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    public User createUser(CreateUserRequest request) { ... }
    public User authenticate(String email, String password) { ... }
}
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

import bcrypt
import jwt

from repositories.user_repository import UserRepository
from models.user import User
from settings import get_settings

settings = get_settings()


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails"""
    pass


class UserService:
    """
    User service for authentication and user management.

    Educational comparison:
    - FastAPI: Manual JWT implementation with bcrypt
    - Spring Boot: Spring Security with auto configuration
    - Password hashing: bcrypt vs PBKDF2/SCrypt
    - JWT tokens: Manual vs framework-provided
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.jwt_secret = settings.jwt_secret_key
        self.jwt_algorithm = "HS256"
        self.token_expire_hours = 24

    def create_user(self, email: str, password: str, first_name: str,
                   last_name: str, role: str = "user") -> User:
        """
        Create a new user account.

        Business rules:
        - Email must be unique
        - Password must meet security requirements
        - Email format validation
        - Role validation

        Spring Boot equivalent:
        @Transactional
        public User createUser(CreateUserRequest request) {
            if (userRepository.existsByEmail(request.getEmail())) {
                throw new BusinessException("Email already exists");
            }

            User user = new User();
            user.setEmail(request.getEmail());
            user.setPassword(passwordEncoder.encode(request.getPassword()));
            user.setFirstName(request.getFirstName());
            user.setLastName(request.getLastName());
            user.setRole(request.getRole());

            return userRepository.save(user);
        }

        Args:
            email: User email address
            password: Plain text password
            first_name: User's first name
            last_name: User's last name
            role: User role (admin, manager, user)

        Returns:
            Created user entity

        Raises:
            ValueError: If validation fails
        """
        # Validate email format
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")

        # Check if email already exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError(f"User with email '{email}' already exists")

        # Validate password strength
        self._validate_password(password)

        # Validate role
        if role not in ["admin", "manager", "user"]:
            raise ValueError(f"Invalid role: {role}")

        # Hash password
        hashed_password = self._hash_password(password)

        # Create user
        user = self.user_repo.create(
            email=email.lower().strip(),
            password_hash=hashed_password,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role=role,
            is_active=True
        )

        return user

    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.

        Spring Boot equivalent:
        public Authentication authenticate(Authentication authentication) {
            String email = authentication.getName();
            String password = authentication.getCredentials().toString();

            User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new BadCredentialsException("Invalid credentials"));

            if (!passwordEncoder.matches(password, user.getPassword())) {
                throw new BadCredentialsException("Invalid credentials");
            }

            return new UsernamePasswordAuthenticationToken(user, null, user.getAuthorities());
        }

        Args:
            email: User email
            password: Plain text password

        Returns:
            Authenticated user entity

        Raises:
            AuthenticationError: If authentication fails
        """
        if not email or not password:
            raise AuthenticationError("Email and password are required")

        # Get user by email
        user = self.user_repo.get_by_email(email.lower().strip())
        if not user:
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        # Verify password
        if not self._verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        # Update last login
        self.user_repo.update_last_login(user.id, datetime.utcnow())

        return user

    def generate_access_token(self, user: User) -> str:
        """
        Generate JWT access token for authenticated user.

        Args:
            user: Authenticated user

        Returns:
            JWT token string
        """
        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expire_hours),
            "iat": datetime.utcnow(),
            "type": "access"
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    def generate_refresh_token(self, user: User) -> str:
        """
        Generate JWT refresh token for token renewal.

        Args:
            user: Authenticated user

        Returns:
            Refresh token string
        """
        payload = {
            "user_id": str(user.id),
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT access token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            if payload.get("type") != "access":
                raise AuthenticationError("Invalid token type")

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        try:
            payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")

            user_id = UUID(payload["user_id"])
            user = self.user_repo.get_by_id(user_id)

            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            return self.generate_access_token(user)

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
            raise AuthenticationError("Invalid refresh token")

    def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.

        Args:
            token: JWT access token

        Returns:
            Current user entity

        Raises:
            AuthenticationError: If token is invalid or user not found
        """
        payload = self.verify_access_token(token)
        user_id = UUID(payload["user_id"])

        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        return user

    def change_password(self, user_id: UUID, current_password: str, new_password: str) -> None:
        """
        Change user password.

        Args:
            user_id: User identifier
            current_password: Current password for verification
            new_password: New password

        Raises:
            AuthenticationError: If current password is incorrect
            ValueError: If new password doesn't meet requirements
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not self._verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        # Validate new password
        self._validate_password(new_password)

        # Hash and update password
        new_password_hash = self._hash_password(new_password)
        self.user_repo.update_password(user_id, new_password_hash)

    def reset_password(self, email: str) -> str:
        """
        Generate password reset token.

        Args:
            email: User email

        Returns:
            Password reset token

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_email(email.lower().strip())
        if not user:
            raise ValueError("User not found")

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Store reset token (in a real app, this would be in a separate table)
        self.user_repo.store_reset_token(user.id, reset_token, expires_at)

        return reset_token

    def confirm_password_reset(self, reset_token: str, new_password: str) -> None:
        """
        Confirm password reset with token.

        Args:
            reset_token: Password reset token
            new_password: New password

        Raises:
            ValueError: If token is invalid or expired
        """
        user_id = self.user_repo.verify_reset_token(reset_token)
        if not user_id:
            raise ValueError("Invalid or expired reset token")

        # Validate new password
        self._validate_password(new_password)

        # Hash and update password
        new_password_hash = self._hash_password(new_password)
        self.user_repo.update_password(user_id, new_password_hash)

        # Clear reset token
        self.user_repo.clear_reset_token(user_id)

    def update_user_profile(self, user_id: UUID, first_name: str = None,
                           last_name: str = None) -> User:
        """
        Update user profile information.

        Args:
            user_id: User identifier
            first_name: New first name
            last_name: New last name

        Returns:
            Updated user entity

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        return self.user_repo.update_profile(
            user_id,
            first_name=first_name.strip() if first_name else None,
            last_name=last_name.strip() if last_name else None
        )

    def deactivate_user(self, user_id: UUID) -> None:
        """
        Deactivate user account.

        Args:
            user_id: User identifier

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        self.user_repo.deactivate(user_id)

    def activate_user(self, user_id: UUID) -> None:
        """
        Activate user account.

        Args:
            user_id: User identifier

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        self.user_repo.activate(user_id)

    def get_all_users(self, skip: int = 0, limit: int = 20,
                     role: Optional[str] = None, active_only: bool = True) -> List[User]:
        """
        Get all users with filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            role: Filter by role
            active_only: Only return active users

        Returns:
            List of user entities
        """
        return self.user_repo.get_all(
            skip=skip,
            limit=limit,
            role=role,
            active_only=active_only
        )

    def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User entity

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    def check_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has specific permission.

        Args:
            user: User entity
            permission: Permission to check

        Returns:
            True if user has permission
        """
        # Simple role-based permissions
        permissions = {
            "admin": ["*"],  # All permissions
            "manager": [
                "read_users", "read_employees", "write_employees",
                "read_time_entries", "write_time_entries", "read_dashboard"
            ],
            "user": [
                "read_employees", "read_time_entries", "write_own_time_entries"
            ]
        }

        user_permissions = permissions.get(user.role, [])
        return "*" in user_permissions or permission in user_permissions

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def _validate_password(self, password: str) -> None:
        """
        Validate password strength.

        Requirements:
        - At least 8 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains digit
        - Contains special character
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            raise ValueError("Password must contain at least one special character")

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


# Educational Notes: User Service Design
#
# 1. Password Security:
#    - bcrypt for password hashing (vs plain text or MD5)
#    - Salt generation for each password
#    - Password strength validation
#
# 2. JWT Token Management:
#    - Access tokens for API authentication
#    - Refresh tokens for token renewal
#    - Token expiration and validation
#
# 3. Authentication vs Authorization:
#    - Authentication: Who are you? (login/password)
#    - Authorization: What can you do? (permissions/roles)
#    - Separation of concerns in service methods
#
# 4. Security Best Practices:
#    - Email normalization (lowercase, trim)
#    - Password reset token expiration
#    - Account activation/deactivation
#    - Permission-based access control
#
# 5. Error Handling:
#    - Specific exception types for different failures
#    - Consistent error messages for security
#    - Logging security events (in production)
#
# 6. Spring Boot Comparison:
#    - Manual JWT vs Spring Security auto-config
#    - Custom user service vs UserDetailsService
#    - Role-based permissions vs @PreAuthorize annotations