"""
Upload Service
File upload and CSV processing service

Provides functionality for handling file uploads, CSV parsing,
data validation, and background processing of large datasets.

Key features:
- CSV file parsing and validation
- Background job processing for large uploads
- Upload status tracking
- Template generation for CSV formats
- Integration with local storage service
"""

import csv
import io
import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Any, BinaryIO, Tuple
from uuid import UUID
from pathlib import Path

from models.employee import Employee
from models.time_entry import TimeEntry
from models.department import Department
from repositories.employee_repository import EmployeeRepository
from repositories.time_entry_repository import TimeEntryRepository
from repositories.department_repository import DepartmentRepository
from services.local_storage_service import LocalStorageService
from services.local_job_service import LocalJobService, JobPriority


class UploadError(Exception):
    """Raised when upload processing fails"""
    pass


class ValidationError(Exception):
    """Raised when data validation fails"""
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or []


class UploadResult:
    """Upload processing result"""
    def __init__(self, upload_id: str, status: str = "pending"):
        self.upload_id = upload_id
        self.status = status
        self.file_name: Optional[str] = None
        self.file_size: Optional[int] = None
        self.total_records: int = 0
        self.processed_records: int = 0
        self.successful_records: int = 0
        self.failed_records: int = 0
        self.errors: List[Dict[str, Any]] = []
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "upload_id": self.upload_id,
            "status": self.status,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "successful_records": self.successful_records,
            "failed_records": self.failed_records,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadResult':
        """Create from dictionary"""
        result = cls(data["upload_id"], data["status"])
        result.file_name = data.get("file_name")
        result.file_size = data.get("file_size")
        result.total_records = data.get("total_records", 0)
        result.processed_records = data.get("processed_records", 0)
        result.successful_records = data.get("successful_records", 0)
        result.failed_records = data.get("failed_records", 0)
        result.errors = data.get("errors", [])
        result.created_at = datetime.fromisoformat(data["created_at"])
        result.started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        result.completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        return result


class UploadService:
    """
    Service for handling file uploads and CSV processing.

    Supports:
    - Employee CSV imports
    - Time entry CSV imports
    - Background processing for large files
    - Validation and error reporting
    - Upload status tracking
    """

    def __init__(self, employee_repo: EmployeeRepository,
                 time_entry_repo: TimeEntryRepository,
                 department_repo: DepartmentRepository,
                 storage_service: LocalStorageService,
                 job_service: LocalJobService):
        self.employee_repo = employee_repo
        self.time_entry_repo = time_entry_repo
        self.department_repo = department_repo
        self.storage_service = storage_service
        self.job_service = job_service

        # Upload results cache
        self.upload_results: Dict[str, UploadResult] = {}

        # Register background job handlers
        self.job_service.register_task("process_employee_upload", self._process_employee_upload_job)
        self.job_service.register_task("process_time_entry_upload", self._process_time_entry_upload_job)

        # Load existing upload results
        self._load_upload_results()

    def upload_employees_csv(self, file_data: BinaryIO, file_name: str,
                           validate_only: bool = False) -> UploadResult:
        """
        Upload and process employee CSV file.

        CSV Format:
        name,email,position,department,hire_date
        John Doe,john@example.com,Senior Attorney,Corporate Law,2023-01-15
        Jane Smith,jane@example.com,Paralegal,Litigation,2023-02-01

        Args:
            file_data: CSV file data
            file_name: Original file name
            validate_only: If True, only validate without saving

        Returns:
            Upload result with processing status
        """
        upload_id = str(uuid.uuid4())
        result = UploadResult(upload_id, "pending")
        result.file_name = file_name

        try:
            # Store file
            file_key = f"uploads/employees/{upload_id}/{file_name}"
            storage_result = self.storage_service.upload_file(
                file_data, "uploads", file_key, "text/csv"
            )
            result.file_size = storage_result["size"]

            # Read and validate CSV
            file_path = self.storage_service.get_file_path("uploads", file_key)
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_data = list(csv.DictReader(f))

            result.total_records = len(csv_data)

            # Validate CSV structure
            self._validate_employee_csv_structure(csv_data)

            if validate_only:
                result.status = "validated"
                result.completed_at = datetime.utcnow()
            else:
                # Queue background processing for large files
                if len(csv_data) > 100:
                    self.job_service.enqueue_job(
                        "process_employee_upload",
                        {"upload_id": upload_id, "file_path": str(file_path)},
                        priority=JobPriority.HIGH
                    )
                    result.status = "processing"
                else:
                    # Process immediately for small files
                    self._process_employee_csv(result, csv_data)

            self.upload_results[upload_id] = result
            self._save_upload_result(result)

            return result

        except Exception as e:
            result.status = "failed"
            result.errors.append({
                "type": "system_error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            result.completed_at = datetime.utcnow()
            self.upload_results[upload_id] = result
            self._save_upload_result(result)
            return result

    def upload_time_entries_csv(self, file_data: BinaryIO, file_name: str,
                              validate_only: bool = False) -> UploadResult:
        """
        Upload and process time entries CSV file.

        CSV Format:
        employee_email,date,hours,description,billable
        john@example.com,2023-12-01,8.0,Client meeting and contract review,true
        jane@example.com,2023-12-01,6.5,Research and documentation,false

        Args:
            file_data: CSV file data
            file_name: Original file name
            validate_only: If True, only validate without saving

        Returns:
            Upload result with processing status
        """
        upload_id = str(uuid.uuid4())
        result = UploadResult(upload_id, "pending")
        result.file_name = file_name

        try:
            # Store file
            file_key = f"uploads/time-entries/{upload_id}/{file_name}"
            storage_result = self.storage_service.upload_file(
                file_data, "uploads", file_key, "text/csv"
            )
            result.file_size = storage_result["size"]

            # Read and validate CSV
            file_path = self.storage_service.get_file_path("uploads", file_key)
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_data = list(csv.DictReader(f))

            result.total_records = len(csv_data)

            # Validate CSV structure
            self._validate_time_entry_csv_structure(csv_data)

            if validate_only:
                result.status = "validated"
                result.completed_at = datetime.utcnow()
            else:
                # Queue background processing for large files
                if len(csv_data) > 100:
                    self.job_service.enqueue_job(
                        "process_time_entry_upload",
                        {"upload_id": upload_id, "file_path": str(file_path)},
                        priority=JobPriority.HIGH
                    )
                    result.status = "processing"
                else:
                    # Process immediately for small files
                    self._process_time_entry_csv(result, csv_data)

            self.upload_results[upload_id] = result
            self._save_upload_result(result)

            return result

        except Exception as e:
            result.status = "failed"
            result.errors.append({
                "type": "system_error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            result.completed_at = datetime.utcnow()
            self.upload_results[upload_id] = result
            self._save_upload_result(result)
            return result

    def get_upload_status(self, upload_id: str) -> Optional[UploadResult]:
        """Get upload processing status"""
        return self.upload_results.get(upload_id)

    def get_upload_history(self, limit: int = 50) -> List[UploadResult]:
        """Get upload history"""
        results = list(self.upload_results.values())
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]

    def generate_employee_template(self) -> str:
        """Generate CSV template for employee uploads"""
        template = [
            ["name", "email", "position", "department", "hire_date"],
            ["John Doe", "john@example.com", "Senior Attorney", "Corporate Law", "2023-01-15"],
            ["Jane Smith", "jane@example.com", "Paralegal", "Litigation", "2023-02-01"]
        ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(template)
        return output.getvalue()

    def generate_time_entry_template(self) -> str:
        """Generate CSV template for time entry uploads"""
        template = [
            ["employee_email", "date", "hours", "description", "billable"],
            ["john@example.com", "2023-12-01", "8.0", "Client meeting and contract review", "true"],
            ["jane@example.com", "2023-12-01", "6.5", "Research and documentation", "false"]
        ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(template)
        return output.getvalue()

    def _validate_employee_csv_structure(self, csv_data: List[Dict[str, Any]]) -> None:
        """Validate employee CSV structure"""
        if not csv_data:
            raise ValidationError("CSV file is empty")

        required_fields = {"name", "email", "position", "department"}
        optional_fields = {"hire_date"}
        all_fields = required_fields | optional_fields

        # Check first row for required fields
        first_row = csv_data[0]
        missing_fields = required_fields - set(first_row.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

        # Check for unexpected fields
        extra_fields = set(first_row.keys()) - all_fields
        if extra_fields:
            raise ValidationError(f"Unexpected fields: {', '.join(extra_fields)}")

        # Validate data types and formats
        errors = []
        for i, row in enumerate(csv_data, 1):
            row_errors = self._validate_employee_row(row, i)
            errors.extend(row_errors)

        if errors:
            raise ValidationError("Validation errors found", errors)

    def _validate_time_entry_csv_structure(self, csv_data: List[Dict[str, Any]]) -> None:
        """Validate time entry CSV structure"""
        if not csv_data:
            raise ValidationError("CSV file is empty")

        required_fields = {"employee_email", "date", "hours", "description", "billable"}

        # Check first row for required fields
        first_row = csv_data[0]
        missing_fields = required_fields - set(first_row.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate data types and formats
        errors = []
        for i, row in enumerate(csv_data, 1):
            row_errors = self._validate_time_entry_row(row, i)
            errors.extend(row_errors)

        if errors:
            raise ValidationError("Validation errors found", errors)

    def _validate_employee_row(self, row: Dict[str, Any], row_num: int) -> List[Dict[str, Any]]:
        """Validate individual employee row"""
        errors = []

        # Name validation
        if not row.get("name", "").strip():
            errors.append({
                "row": row_num,
                "field": "name",
                "message": "Name is required"
            })

        # Email validation
        email = row.get("email", "").strip()
        if not email:
            errors.append({
                "row": row_num,
                "field": "email",
                "message": "Email is required"
            })
        elif "@" not in email:
            errors.append({
                "row": row_num,
                "field": "email",
                "message": "Invalid email format"
            })

        # Hire date validation
        hire_date = row.get("hire_date", "").strip()
        if hire_date:
            try:
                datetime.strptime(hire_date, "%Y-%m-%d")
            except ValueError:
                errors.append({
                    "row": row_num,
                    "field": "hire_date",
                    "message": "Invalid date format (use YYYY-MM-DD)"
                })

        return errors

    def _validate_time_entry_row(self, row: Dict[str, Any], row_num: int) -> List[Dict[str, Any]]:
        """Validate individual time entry row"""
        errors = []

        # Employee email validation
        email = row.get("employee_email", "").strip()
        if not email:
            errors.append({
                "row": row_num,
                "field": "employee_email",
                "message": "Employee email is required"
            })

        # Date validation
        date_str = row.get("date", "").strip()
        if not date_str:
            errors.append({
                "row": row_num,
                "field": "date",
                "message": "Date is required"
            })
        else:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                errors.append({
                    "row": row_num,
                    "field": "date",
                    "message": "Invalid date format (use YYYY-MM-DD)"
                })

        # Hours validation
        hours_str = row.get("hours", "").strip()
        if not hours_str:
            errors.append({
                "row": row_num,
                "field": "hours",
                "message": "Hours is required"
            })
        else:
            try:
                hours = float(hours_str)
                if hours <= 0 or hours > 24:
                    errors.append({
                        "row": row_num,
                        "field": "hours",
                        "message": "Hours must be between 0.1 and 24.0"
                    })
            except ValueError:
                errors.append({
                    "row": row_num,
                    "field": "hours",
                    "message": "Invalid hours format (use decimal number)"
                })

        # Description validation
        description = row.get("description", "").strip()
        if not description:
            errors.append({
                "row": row_num,
                "field": "description",
                "message": "Description is required"
            })
        elif len(description) < 10:
            errors.append({
                "row": row_num,
                "field": "description",
                "message": "Description must be at least 10 characters"
            })

        # Billable validation
        billable_str = row.get("billable", "").strip().lower()
        if billable_str not in ["true", "false", "1", "0", "yes", "no"]:
            errors.append({
                "row": row_num,
                "field": "billable",
                "message": "Billable must be true/false, yes/no, or 1/0"
            })

        return errors

    def _process_employee_csv(self, result: UploadResult, csv_data: List[Dict[str, Any]]) -> None:
        """Process employee CSV data"""
        result.status = "processing"
        result.started_at = datetime.utcnow()

        for i, row in enumerate(csv_data, 1):
            try:
                # Get or create department
                dept_name = row["department"].strip()
                department = self.department_repo.get_by_name(dept_name)
                if not department:
                    department = self.department_repo.create(name=dept_name)

                # Parse hire date
                hire_date = None
                if row.get("hire_date", "").strip():
                    hire_date = datetime.strptime(row["hire_date"], "%Y-%m-%d").date()

                # Create employee
                self.employee_repo.create(
                    name=row["name"].strip(),
                    email=row["email"].strip().lower(),
                    position=row["position"].strip(),
                    department_id=department.id,
                    hire_date=hire_date
                )

                result.successful_records += 1

            except Exception as e:
                result.failed_records += 1
                result.errors.append({
                    "row": i,
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

            result.processed_records += 1

        result.status = "completed"
        result.completed_at = datetime.utcnow()

    def _process_time_entry_csv(self, result: UploadResult, csv_data: List[Dict[str, Any]]) -> None:
        """Process time entry CSV data"""
        result.status = "processing"
        result.started_at = datetime.utcnow()

        for i, row in enumerate(csv_data, 1):
            try:
                # Find employee by email
                employee = self.employee_repo.get_by_email(row["employee_email"].strip().lower())
                if not employee:
                    raise ValueError(f"Employee not found: {row['employee_email']}")

                # Parse data
                entry_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                hours = float(row["hours"])
                description = row["description"].strip()
                billable_str = row["billable"].strip().lower()
                billable = billable_str in ["true", "1", "yes"]

                # Create time entry
                self.time_entry_repo.create(
                    employee_id=employee.id,
                    date=entry_date,
                    hours=hours,
                    description=description,
                    billable=billable
                )

                result.successful_records += 1

            except Exception as e:
                result.failed_records += 1
                result.errors.append({
                    "row": i,
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

            result.processed_records += 1

        result.status = "completed"
        result.completed_at = datetime.utcnow()

    def _process_employee_upload_job(self, upload_id: str, file_path: str) -> None:
        """Background job for processing employee uploads"""
        result = self.upload_results.get(upload_id)
        if not result:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_data = list(csv.DictReader(f))

            self._process_employee_csv(result, csv_data)

        except Exception as e:
            result.status = "failed"
            result.errors.append({
                "type": "processing_error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            result.completed_at = datetime.utcnow()

        self._save_upload_result(result)

    def _process_time_entry_upload_job(self, upload_id: str, file_path: str) -> None:
        """Background job for processing time entry uploads"""
        result = self.upload_results.get(upload_id)
        if not result:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_data = list(csv.DictReader(f))

            self._process_time_entry_csv(result, csv_data)

        except Exception as e:
            result.status = "failed"
            result.errors.append({
                "type": "processing_error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            result.completed_at = datetime.utcnow()

        self._save_upload_result(result)

    def _save_upload_result(self, result: UploadResult) -> None:
        """Save upload result to storage"""
        file_key = f"upload_results/{result.upload_id}.json"
        data = json.dumps(result.to_dict(), indent=2)
        self.storage_service.upload_file(
            io.BytesIO(data.encode('utf-8')),
            "system",
            file_key,
            "application/json"
        )

    def _load_upload_results(self) -> None:
        """Load existing upload results"""
        try:
            files = self.storage_service.list_files("system", "upload_results/")
            for file_info in files:
                if file_info["key"].endswith(".json"):
                    try:
                        file_data = self.storage_service.download_file("system", file_info["key"])
                        data = json.loads(file_data.read().decode('utf-8'))
                        result = UploadResult.from_dict(data)
                        self.upload_results[result.upload_id] = result
                    except Exception:
                        continue  # Skip corrupted files
        except Exception:
            pass  # No existing results