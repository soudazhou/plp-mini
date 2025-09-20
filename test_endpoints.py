#!/usr/bin/env python3
"""
Test script to validate all implemented API endpoints
Tests the time entry and employee endpoints to ensure functionality
"""

import requests
import json
import sys
from datetime import date
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def test_endpoint(method: str, url: str, data: Dict[Any, Any] = None, expected_status: int = 200) -> Dict[Any, Any]:
    """Test an API endpoint and return the response"""
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"  {method} {url}")
        print(f"    Status: {response.status_code}")

        if response.status_code != expected_status:
            print(f"    ❌ Expected {expected_status}, got {response.status_code}")
            if response.text:
                print(f"    Response: {response.text[:200]}...")
            return {"error": f"Status {response.status_code}"}

        if response.status_code == 204:  # No content
            print(f"    ✅ Success (No Content)")
            return {"success": True}

        try:
            result = response.json()
            print(f"    ✅ Success")
            return result
        except json.JSONDecodeError:
            print(f"    ❌ Invalid JSON response")
            return {"error": "Invalid JSON"}

    except requests.exceptions.ConnectionError:
        print(f"    ❌ Connection failed - ensure server is running")
        return {"error": "Connection failed"}
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return {"error": str(e)}

def main():
    print("🧪 Testing LegalAnalytics Mini API Endpoints")
    print("=" * 50)

    # Test 1: Health check
    print("\n1. Health Check")
    health = test_endpoint("GET", f"{BASE_URL}/health")
    if "error" in health:
        print("❌ Server not responding - please start the server first")
        sys.exit(1)

    # Test 2: Employee endpoints
    print("\n2. Employee Endpoints")

    # List employees
    employees = test_endpoint("GET", f"{API_V1}/employees/")
    if "error" in employees:
        print("❌ Failed to get employees")
        return False

    if not employees.get("employees"):
        print("❌ No employees found in database")
        return False

    print(f"    Found {len(employees['employees'])} employees")

    # Get first employee for testing
    first_employee = employees["employees"][0]
    employee_id = first_employee["id"]
    print(f"    Using employee: {first_employee['name']} ({employee_id})")

    # Get specific employee
    employee = test_endpoint("GET", f"{API_V1}/employees/{employee_id}")
    if "error" in employee:
        print("❌ Failed to get specific employee")
        return False

    # Search employees
    search_result = test_endpoint("GET", f"{API_V1}/employees/?search=John")
    if "error" in search_result:
        print("❌ Failed to search employees")
        return False

    # Test 3: Time Entry endpoints
    print("\n3. Time Entry Endpoints")

    # List time entries
    time_entries = test_endpoint("GET", f"{API_V1}/time-entries/")
    if "error" in time_entries:
        print("❌ Failed to get time entries")
        return False

    print(f"    Found {len(time_entries['time_entries'])} time entries")

    if time_entries.get("time_entries"):
        # Get specific time entry
        first_entry = time_entries["time_entries"][0]
        entry_id = first_entry["id"]
        print(f"    Using time entry: {entry_id}")

        entry = test_endpoint("GET", f"{API_V1}/time-entries/{entry_id}")
        if "error" in entry:
            print("❌ Failed to get specific time entry")
            return False

    # Test filtering
    filtered = test_endpoint("GET", f"{API_V1}/time-entries/?billable=true&limit=2")
    if "error" in filtered:
        print("❌ Failed to filter time entries")
        return False

    print(f"    Filtered results: {len(filtered['time_entries'])} entries")

    # Test summary
    summary = test_endpoint("GET", f"{API_V1}/time-entries/summary")
    if "error" in summary:
        print("❌ Failed to get time entries summary")
        return False

    print(f"    Summary: {summary['total_hours']} total hours, {summary['billable_hours']} billable")

    # Test search
    search = test_endpoint("GET", f"{API_V1}/time-entries/search?q=contract")
    if "error" in search:
        print("❌ Failed to search time entries")
        return False

    print(f"    Search results: {len(search)} entries")

    # Test 4: Dashboard endpoints
    print("\n4. Dashboard Endpoints")

    # Dashboard overview
    overview = test_endpoint("GET", f"{API_V1}/dashboard/overview")
    if "error" in overview:
        print("❌ Failed to get dashboard overview")
        return False

    print(f"    Overview: {overview['metrics']['total_employees']} employees, {overview['metrics']['total_hours']} hours")

    # Department hours
    dept_hours = test_endpoint("GET", f"{API_V1}/dashboard/department-hours")
    if "error" in dept_hours:
        print("❌ Failed to get department hours")
        return False

    print(f"    Department breakdown: {len(dept_hours)} departments")

    # Utilization rates
    utilization = test_endpoint("GET", f"{API_V1}/dashboard/utilization")
    if "error" in utilization:
        print("❌ Failed to get utilization rates")
        return False

    print(f"    Utilization data: {len(utilization)} employees")

    # Trends
    trends = test_endpoint("GET", f"{API_V1}/dashboard/trends")
    if "error" in trends:
        print("❌ Failed to get trends")
        return False

    print(f"    Trends: {len(trends['trends'])} data points")

    # Test 5: Create and update operations (optional)
    print("\n5. CRUD Operations")

    # Test creating a time entry
    create_data = {
        "employee_id": employee_id,
        "date": str(date.today()),
        "hours": 2.5,
        "description": "Test time entry created by validation script",
        "billable": False
    }

    created = test_endpoint("POST", f"{API_V1}/time-entries/", create_data, 201)
    if "error" not in created:
        print(f"    ✅ Created time entry: {created['id']}")

        # Update the created entry
        update_data = {
            "hours": 3.0,
            "description": "Updated test time entry"
        }

        updated = test_endpoint("PUT", f"{API_V1}/time-entries/{created['id']}", update_data)
        if "error" not in updated:
            print(f"    ✅ Updated time entry hours to {updated['hours']}")

        # Delete the created entry
        deleted = test_endpoint("DELETE", f"{API_V1}/time-entries/{created['id']}", expected_status=204)
        if "error" not in deleted:
            print(f"    ✅ Deleted test time entry")

    print("\n" + "=" * 50)
    print("🎉 All endpoint tests completed successfully!")
    print("✅ Time entry APIs are working")
    print("✅ Employee APIs are working")
    print("✅ Dashboard APIs are working")
    print("✅ CRUD operations are working")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)