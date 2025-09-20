#!/usr/bin/env python3
"""
Database Seeding Script for LegalAnalytics Mini

This script populates the database with sample data for development
and testing purposes. Educational comparison with Spring Boot data.sql
and @Sql test annotations.

Usage:
    python scripts/seed_data.py [--env development|testing]

Spring Boot Equivalent:
- data.sql files in src/main/resources
- @Sql annotations in test classes
- @DataJpaTest with @AutoConfigureTestDatabase
"""

import asyncio
import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models.department import Department
from models.employee import Employee
from models.time_entry import TimeEntry
from models.user import User, UserRole
from settings import get_settings


class DatabaseSeeder:
    """
    Database seeding utility class.

    Similar to Spring Boot's DataLoader or CommandLineRunner
    implementations for loading sample data.
    """

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.settings = get_settings()

        # Create database engine and session
        self.engine = create_engine(
            self.settings.database_url,
            echo=self.settings.database.echo,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """
        Create all database tables.

        Spring Boot equivalent:
        spring.jpa.hibernate.ddl-auto=create-drop
        """
        print("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        print("✅ Tables created successfully")

    def clear_data(self) -> None:
        """
        Clear all existing data (for testing environment).

        Spring Boot equivalent:
        @Sql(scripts = "classpath:cleanup.sql",
             executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
        """
        if self.environment == "testing":
            print("Clearing existing data...")
            with self.SessionLocal() as session:
                session.query(TimeEntry).delete()
                session.query(Employee).delete()
                session.query(User).delete()
                session.query(Department).delete()
                session.commit()
            print("✅ Data cleared successfully")

    def seed_departments(self) -> List[Department]:
        """
        Create sample departments.

        Spring Boot equivalent:
        @Component
        public class DepartmentDataLoader implements CommandLineRunner {
            @Override
            public void run(String... args) {
                if (departmentRepository.count() == 0) {
                    // Create departments
                }
            }
        }
        """
        print("Seeding departments...")

        departments_data = [
            {
                "name": "Corporate Law",
                "description": "Handles corporate transactions, mergers, acquisitions, and business formation matters."
            },
            {
                "name": "Litigation",
                "description": "Manages civil litigation, disputes, and court proceedings for clients."
            },
            {
                "name": "Employment Law",
                "description": "Specializes in employment contracts, workplace disputes, and labor relations."
            },
            {
                "name": "Intellectual Property",
                "description": "Focuses on patents, trademarks, copyrights, and trade secrets protection."
            },
        ]

        departments = []
        with self.SessionLocal() as session:
            for dept_data in departments_data:
                # Check if department already exists
                existing = session.query(Department).filter_by(name=dept_data["name"]).first()
                if not existing:
                    department = Department(**dept_data)
                    session.add(department)
                    departments.append(department)
                else:
                    departments.append(existing)

            session.commit()
            print(f"✅ Created {len(departments_data)} departments")
            return departments

    def seed_users_and_employees(self, departments: List[Department]) -> List[Employee]:
        """
        Create sample users and employees.

        Demonstrates the relationship between User (authentication)
        and Employee (business entity) similar to Spring Security
        UserDetails vs business entity separation.
        """
        print("Seeding users and employees...")

        employees_data = [
            {
                "name": "Sarah Johnson",
                "email": "sarah.johnson@lawfirm.com",
                "hire_date": date(2020, 3, 15),
                "department": "Corporate Law",
                "user": {
                    "username": "sarah.johnson",
                    "role": UserRole.PARTNER,
                    "is_active": True,
                }
            },
            {
                "name": "Michael Chen",
                "email": "michael.chen@lawfirm.com",
                "hire_date": date(2021, 8, 22),
                "department": "Litigation",
                "user": {
                    "username": "michael.chen",
                    "role": UserRole.LAWYER,
                    "is_active": True,
                }
            },
            {
                "name": "Emily Rodriguez",
                "email": "emily.rodriguez@lawfirm.com",
                "hire_date": date(2019, 1, 10),
                "department": "Employment Law",
                "user": {
                    "username": "emily.rodriguez",
                    "role": UserRole.HR_ADMIN,
                    "is_active": True,
                }
            },
            {
                "name": "David Kim",
                "email": "david.kim@lawfirm.com",
                "hire_date": date(2022, 5, 1),
                "department": "Intellectual Property",
                "user": {
                    "username": "david.kim",
                    "role": UserRole.LAWYER,
                    "is_active": True,
                }
            },
            {
                "name": "Lisa Thompson",
                "email": "lisa.thompson@lawfirm.com",
                "hire_date": date(2021, 11, 8),
                "department": "Corporate Law",
                "user": {
                    "username": "lisa.thompson",
                    "role": UserRole.LAWYER,
                    "is_active": True,
                }
            },
            # Employee without user account (for testing)
            {
                "name": "Robert Wilson",
                "email": "robert.wilson@lawfirm.com",
                "hire_date": date(2023, 2, 20),
                "department": "Litigation",
                "user": None
            },
        ]

        # Create department name to object mapping
        dept_map = {dept.name: dept for dept in departments}

        employees = []
        with self.SessionLocal() as session:
            for emp_data in employees_data:
                # Check if employee already exists
                existing_emp = session.query(Employee).filter_by(email=emp_data["email"]).first()
                if existing_emp:
                    employees.append(existing_emp)
                    continue

                # Create employee
                employee = Employee(
                    name=emp_data["name"],
                    email=emp_data["email"],
                    hire_date=emp_data["hire_date"],
                    department_id=dept_map[emp_data["department"]].id
                )
                session.add(employee)
                session.flush()  # Get employee ID

                # Create user if specified
                if emp_data["user"]:
                    user_data = emp_data["user"]
                    existing_user = session.query(User).filter_by(username=user_data["username"]).first()
                    if not existing_user:
                        user = User(
                            username=user_data["username"],
                            email=emp_data["email"],
                            role=user_data["role"],
                            is_active=user_data["is_active"],
                            employee_id=employee.id
                        )
                        # Set a simple password for development
                        user.set_password("password123")
                        session.add(user)

                employees.append(employee)

            session.commit()
            print(f"✅ Created {len(employees_data)} employees with users")
            return employees

    def seed_time_entries(self, employees: List[Employee]) -> None:
        """
        Create sample time entries for the last 30 days.

        Generates realistic billable hours data for dashboard analytics.
        """
        print("Seeding time entries...")

        # Sample work descriptions for different departments
        work_descriptions = {
            "Corporate Law": [
                "Reviewed merger agreement for ABC Corp acquisition",
                "Drafted corporate bylaws for new entity formation",
                "Legal due diligence for private equity transaction",
                "Negotiated terms of joint venture agreement",
                "Prepared board resolutions and corporate governance documents",
            ],
            "Litigation": [
                "Drafted motion for summary judgment in contract dispute",
                "Conducted client interview and case assessment",
                "Reviewed discovery documents for patent infringement case",
                "Prepared deposition outline for key witness testimony",
                "Research case law for employment discrimination matter",
            ],
            "Employment Law": [
                "Drafted employment agreement for executive position",
                "Reviewed employee handbook for compliance updates",
                "Advised client on workplace harassment investigation",
                "Prepared severance agreement and release documents",
                "Conducted legal research on remote work policies",
            ],
            "Intellectual Property": [
                "Drafted patent application for software innovation",
                "Trademark search and registration filing",
                "Reviewed licensing agreement for technology transfer",
                "Prepared copyright registration for creative works",
                "Analyzed patent infringement claims and defenses",
            ],
        }

        matter_codes = [
            "ABC-001", "XYZ-205", "DEF-442", "GHI-789", "JKL-156",
            "MNO-333", "PQR-678", "STU-901", "VWX-234", "YZA-567",
        ]

        import random
        random.seed(42)  # Consistent data for testing

        entries_created = 0
        with self.SessionLocal() as session:
            # Generate entries for last 30 days
            start_date = date.today() - timedelta(days=30)

            for employee in employees:
                if not employee.department:
                    continue

                dept_descriptions = work_descriptions.get(employee.department.name, work_descriptions["Corporate Law"])

                # Generate 15-25 entries per employee over 30 days
                num_entries = random.randint(15, 25)

                for _ in range(num_entries):
                    # Random date in the last 30 days (excluding weekends for most entries)
                    days_back = random.randint(0, 29)
                    entry_date = start_date + timedelta(days=days_back)

                    # Skip some weekends (80% of weekend entries)
                    if entry_date.weekday() >= 5 and random.random() < 0.8:
                        continue

                    # Check if entry already exists for this date
                    existing = session.query(TimeEntry).filter_by(
                        employee_id=employee.id,
                        date=entry_date
                    ).first()
                    if existing:
                        continue

                    # Random hours (most entries between 6-9 hours)
                    if random.random() < 0.1:  # 10% chance of short day
                        hours = Decimal(str(round(random.uniform(2.0, 5.0), 2)))
                    elif random.random() < 0.1:  # 10% chance of long day
                        hours = Decimal(str(round(random.uniform(10.0, 12.0), 2)))
                    else:  # 80% normal day
                        hours = Decimal(str(round(random.uniform(6.0, 9.0), 2)))

                    # 90% of entries are billable
                    billable = random.random() < 0.9

                    # Random description and matter code
                    description = random.choice(dept_descriptions)
                    matter_code = random.choice(matter_codes) if random.random() < 0.8 else None

                    time_entry = TimeEntry(
                        employee_id=employee.id,
                        date=entry_date,
                        hours=hours,
                        description=description,
                        billable=billable,
                        matter_code=matter_code
                    )
                    session.add(time_entry)
                    entries_created += 1

            session.commit()
            print(f"✅ Created {entries_created} time entries")

    def create_admin_user(self) -> None:
        """
        Create default admin user for system access.

        Spring Boot equivalent:
        @PostConstruct
        public void createDefaultAdmin() {
            if (userRepository.count() == 0) {
                User admin = new User("admin", "admin@system.com", Role.ADMIN);
                userRepository.save(admin);
            }
        }
        """
        print("Creating default admin user...")

        with self.SessionLocal() as session:
            # Check if admin user exists
            admin_user = session.query(User).filter_by(username="admin").first()
            if not admin_user:
                admin = User(
                    username="admin",
                    email="admin@legalanalytics.com",
                    role=UserRole.HR_ADMIN,
                    is_active=True,
                    employee_id=None  # System user, not associated with employee
                )
                admin.set_password("admin123")  # Change in production!
                session.add(admin)
                session.commit()
                print("✅ Created admin user (username: admin, password: admin123)")
            else:
                print("✅ Admin user already exists")

    def run_seeding(self) -> None:
        """
        Execute the complete seeding process.

        Spring Boot equivalent:
        @Component
        @Order(1)
        public class DatabaseSeeder implements CommandLineRunner {
            @Override
            public void run(String... args) {
                seedDepartments();
                seedEmployees();
                seedTimeEntries();
            }
        }
        """
        print(f"🌱 Starting database seeding for {self.environment} environment...")

        try:
            # Create tables if they don't exist
            self.create_tables()

            # Clear data for testing environment
            if self.environment == "testing":
                self.clear_data()

            # Seed data in dependency order
            departments = self.seed_departments()
            employees = self.seed_users_and_employees(departments)
            self.seed_time_entries(employees)
            self.create_admin_user()

            print("🎉 Database seeding completed successfully!")

            # Print summary
            with self.SessionLocal() as session:
                dept_count = session.query(Department).count()
                emp_count = session.query(Employee).count()
                user_count = session.query(User).count()
                entry_count = session.query(TimeEntry).count()

                print("\n📊 Data Summary:")
                print(f"  • Departments: {dept_count}")
                print(f"  • Employees: {emp_count}")
                print(f"  • Users: {user_count}")
                print(f"  • Time Entries: {entry_count}")

        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            raise


def main():
    """
    Main entry point for the seeding script.

    Supports command-line arguments for environment selection.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Seed database with sample data")
    parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="development",
        help="Environment to seed (default: development)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding"
    )

    args = parser.parse_args()

    if args.env == "production":
        print("⚠️  Production seeding is not recommended!")
        response = input("Are you sure you want to continue? (y/N): ")
        if response.lower() != 'y':
            print("Seeding cancelled.")
            return

    seeder = DatabaseSeeder(environment=args.env)

    if args.clear:
        seeder.clear_data()

    seeder.run_seeding()


if __name__ == "__main__":
    main()


# Educational Notes: Database Seeding Patterns
#
# 1. Seeding Strategies:
#    SQLAlchemy: Custom Python scripts with ORM
#    Spring Boot: data.sql, @Sql annotations, CommandLineRunner
#    Both: Programmatic seeding with dependency management
#
# 2. Environment Handling:
#    SQLAlchemy: Command-line arguments or environment variables
#    Spring Boot: Profiles (@Profile annotations)
#    Both: Different data sets per environment
#
# 3. Data Relationships:
#    SQLAlchemy: Manual FK management in seeding order
#    Spring Boot: @Transactional methods with cascading
#    Both: Dependency-aware seeding sequences
#
# 4. Testing Integration:
#    SQLAlchemy: pytest fixtures with database seeding
#    Spring Boot: @DataJpaTest with @Sql annotations
#    Both: Isolated test data for consistent testing
#
# 5. Production Considerations:
#    - Never seed production with test data
#    - Use migration scripts for schema changes
#    - Separate reference data from test data
#    - Consider data privacy and security