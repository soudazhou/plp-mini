"""
Database Initialization Script

Creates all database tables and adds sample data for testing.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import get_settings
from models.base import Base
from models.department import Department
from models.employee import Employee
from models.time_entry import TimeEntry
# from models.user import User  # Commented out for demo

def init_database():
    """Initialize database with tables and sample data."""
    settings = get_settings()

    # Create engine and tables
    engine = create_engine(settings.database_url, echo=True)

    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(Department).count() > 0:
            print("Database already has data. Skipping initialization.")
            return

        print("Adding sample data...")

        # Create departments
        corporate_law = Department(
            id=uuid.uuid4(),
            name="Corporate Law",
            description="Handles corporate legal matters and business transactions"
        )

        litigation = Department(
            id=uuid.uuid4(),
            name="Litigation",
            description="Manages court cases and legal disputes"
        )

        real_estate = Department(
            id=uuid.uuid4(),
            name="Real Estate",
            description="Property law and real estate transactions"
        )

        # Add departments
        db.add_all([corporate_law, litigation, real_estate])
        db.commit()

        # Create employees
        employees_data = [
            {
                "name": "John Smith",
                "email": "john.smith@legalfirm.com",
                "hire_date": date(2020, 1, 15),
                "department_id": corporate_law.id
            },
            {
                "name": "Sarah Johnson",
                "email": "sarah.johnson@legalfirm.com",
                "hire_date": date(2019, 3, 10),
                "department_id": litigation.id
            },
            {
                "name": "Michael Brown",
                "email": "michael.brown@legalfirm.com",
                "hire_date": date(2021, 6, 20),
                "department_id": real_estate.id
            },
            {
                "name": "Emily Davis",
                "email": "emily.davis@legalfirm.com",
                "hire_date": date(2018, 11, 5),
                "department_id": corporate_law.id
            },
            {
                "name": "David Wilson",
                "email": "david.wilson@legalfirm.com",
                "hire_date": date(2022, 2, 1),
                "department_id": litigation.id
            }
        ]

        employees = []
        for emp_data in employees_data:
            employee = Employee(
                id=uuid.uuid4(),
                **emp_data
            )
            employees.append(employee)
            db.add(employee)

        db.commit()

        # Create some sample time entries
        time_entries_data = [
            {
                "employee_id": employees[0].id,
                "date": date(2023, 12, 1),
                "hours": Decimal("8.0"),
                "description": "Reviewed contract terms for client merger deal",
                "billable": True
            },
            {
                "employee_id": employees[0].id,
                "date": date(2023, 12, 2),
                "hours": Decimal("6.5"),
                "description": "Attended team meeting and training session",
                "billable": False
            },
            {
                "employee_id": employees[1].id,
                "date": date(2023, 12, 1),
                "hours": Decimal("7.5"),
                "description": "Prepared court documents for litigation case ABC-123",
                "billable": True
            },
            {
                "employee_id": employees[2].id,
                "date": date(2023, 12, 1),
                "hours": Decimal("8.0"),
                "description": "Property due diligence for commercial real estate transaction",
                "billable": True
            }
        ]

        for entry_data in time_entries_data:
            time_entry = TimeEntry(
                id=uuid.uuid4(),
                **entry_data
            )
            db.add(time_entry)

        db.commit()

        print("✅ Database initialized successfully!")
        print(f"✅ Created {len(employees)} employees")
        print(f"✅ Created 3 departments")
        print(f"✅ Created {len(time_entries_data)} time entries")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()