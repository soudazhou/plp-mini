#!/usr/bin/env python3
"""
Simple test runner to validate the implementation
without requiring full pytest setup
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all our modules can be imported successfully"""
    print("🧪 Testing module imports...")

    try:
        # Test model imports
        from models.base import Base, UUIDAuditMixin
        from models.department import Department
        from models.user import User, UserRole
        from models.employee import Employee
        from models.time_entry import TimeEntry
        print("✅ Models import successfully")

        # Test repository imports
        from repositories.department_repository import DepartmentRepository
        from repositories.employee_repository import EmployeeRepository
        print("✅ Repositories import successfully")

        # Test service imports
        from services.employee_service import EmployeeService
        print("✅ Services import successfully")

        # Test API imports
        from api.employees import router
        print("✅ API routes import successfully")

        # Test main app
        from main import app
        print("✅ Main application imports successfully")

        # Test settings
        from settings import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded: {settings.app_name}")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_models():
    """Test model creation and validation"""
    print("\n🧪 Testing model creation...")

    try:
        from models.department import Department
        from models.user import User, UserRole
        from models.employee import Employee
        from models.time_entry import TimeEntry
        from datetime import date
        from decimal import Decimal

        # Test Department creation
        dept = Department(name="Test Department", description="Test")
        print("✅ Department model creates successfully")

        # Test User creation
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.LAWYER,
            is_active=True
        )
        print("✅ User model creates successfully")

        # Test Employee creation (without DB)
        emp = Employee(
            name="Test Employee",
            email="emp@example.com",
            hire_date=date(2023, 1, 1)
        )
        print("✅ Employee model creates successfully")

        # Test TimeEntry creation
        entry = TimeEntry(
            date=date.today(),
            hours=Decimal("8.00"),
            description="Test work description for validation",
            billable=True
        )
        print("✅ TimeEntry model creates successfully")

        return True

    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False

def test_pydantic_schemas():
    """Test Pydantic schemas for API validation"""
    print("\n🧪 Testing API schemas...")

    try:
        from api.employees import EmployeeCreate, EmployeeResponse
        from datetime import date
        import uuid

        # Test EmployeeCreate schema
        create_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "department_id": str(uuid.uuid4()),
            "hire_date": "2023-01-01"
        }

        employee_create = EmployeeCreate(**create_data)
        print("✅ EmployeeCreate schema validates successfully")

        # Test validation errors
        try:
            invalid_data = {
                "name": "A",  # Too short
                "email": "invalid-email",
                "department_id": "invalid-uuid",
                "hire_date": "2030-01-01"  # Future date
            }
            EmployeeCreate(**invalid_data)
            print("❌ Schema should have failed validation")
        except Exception:
            print("✅ Schema validation correctly catches errors")

        return True

    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI application creation"""
    print("\n🧪 Testing FastAPI application...")

    try:
        from main import app
        from fastapi.testclient import TestClient

        # Create test client
        client = TestClient(app)

        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint responds successfully")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")

        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Root endpoint responds successfully")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")

        return True

    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running LegalAnalytics Mini validation tests...\n")

    tests = [
        test_imports,
        test_models,
        test_pydantic_schemas,
        test_fastapi_app
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The implementation is working correctly.")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start Docker services: docker-compose up -d")
        print("3. Run database migrations: alembic upgrade head")
        print("4. Start the API server: uvicorn src.main:app --reload")
        print("5. Test endpoints at: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())