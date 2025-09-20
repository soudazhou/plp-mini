"""
Upload API Endpoints
T073-T078 - File upload and CSV processing endpoints

FastAPI routes for file upload functionality including CSV processing,
status tracking, and template generation.

Spring Boot equivalent:
@RestController
@RequestMapping("/api/v1/upload")
public class UploadController {
    @PostMapping("/employees")
    public ResponseEntity<UploadResponse> uploadEmployees(@RequestParam MultipartFile file) { ... }

    @GetMapping("/status/{id}")
    public ResponseEntity<UploadStatusResponse> getUploadStatus(@PathVariable String id) { ... }
}
"""

from typing import List, Optional
from uuid import UUID
import io

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from services.upload_service import UploadService, UploadResult, ValidationError
from services.local_storage_service import LocalStorageService, get_storage_service
from services.local_job_service import get_job_service
from repositories.employee_repository import EmployeeRepository
from repositories.time_entry_repository import TimeEntryRepository
from repositories.department_repository import DepartmentRepository


# Router instance
router = APIRouter(prefix="/upload", tags=["upload"])


# Pydantic Models for Request/Response

class UploadResponse(BaseModel):
    """Upload response model"""
    upload_id: str = Field(..., description="Unique upload identifier")
    status: str = Field(..., description="Upload status (pending, processing, completed, failed)")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    total_records: int = Field(..., description="Total records in file")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "12345678-1234-5678-9abc-123456789012",
                "status": "processing",
                "file_name": "employees.csv",
                "file_size": 2048,
                "total_records": 50,
                "message": "File uploaded successfully and is being processed"
            }
        }


class UploadStatusResponse(BaseModel):
    """Upload status response model"""
    upload_id: str
    status: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    errors: List[dict] = []
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_percentage: float = Field(..., description="Processing progress (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "12345678-1234-5678-9abc-123456789012",
                "status": "completed",
                "file_name": "employees.csv",
                "file_size": 2048,
                "total_records": 50,
                "processed_records": 50,
                "successful_records": 48,
                "failed_records": 2,
                "errors": [
                    {"row": 15, "field": "email", "message": "Invalid email format"},
                    {"row": 32, "field": "hire_date", "message": "Invalid date format"}
                ],
                "created_at": "2023-12-01T10:00:00Z",
                "started_at": "2023-12-01T10:00:05Z",
                "completed_at": "2023-12-01T10:02:30Z",
                "progress_percentage": 100.0
            }
        }


class UploadHistoryResponse(BaseModel):
    """Upload history response model"""
    uploads: List[UploadStatusResponse]
    total_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "uploads": [
                    {
                        "upload_id": "12345678-1234-5678-9abc-123456789012",
                        "status": "completed",
                        "file_name": "employees.csv",
                        "total_records": 50,
                        "successful_records": 48,
                        "failed_records": 2,
                        "created_at": "2023-12-01T10:00:00Z",
                        "progress_percentage": 100.0
                    }
                ],
                "total_count": 1
            }
        }


# Dependency injection for service layer
def get_upload_service(db: Session = Depends(get_db)) -> UploadService:
    """Get upload service with dependencies"""
    employee_repo = EmployeeRepository(db)
    time_entry_repo = TimeEntryRepository(db)
    department_repo = DepartmentRepository(db)
    storage_service = get_storage_service()
    job_service = get_job_service()

    return UploadService(
        employee_repo=employee_repo,
        time_entry_repo=time_entry_repo,
        department_repo=department_repo,
        storage_service=storage_service,
        job_service=job_service
    )


# API Endpoints

@router.post("/employees", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_employees(
    file: UploadFile = File(..., description="CSV file with employee data"),
    validate_only: bool = Query(False, description="Only validate without saving"),
    service: UploadService = Depends(get_upload_service)
):
    """
    Upload employee CSV file

    Accepts CSV files with employee data for bulk import.
    Supports validation-only mode for testing file format.

    CSV Format:
    - name: Employee full name (required)
    - email: Employee email address (required)
    - position: Job position/title (required)
    - department: Department name (required)
    - hire_date: Hire date in YYYY-MM-DD format (optional)

    File Processing:
    - Files under 100 records: Processed immediately
    - Files over 100 records: Processed in background
    - Maximum file size: 10MB
    - Supported formats: CSV (text/csv)

    Returns upload ID for status tracking.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('text/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a CSV file."
        )

    # Check file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10MB."
        )

    try:
        # Reset file pointer
        file_data = io.BytesIO(file_content)

        # Process upload
        result = service.upload_employees_csv(file_data, file.filename, validate_only)

        # Generate response message
        if validate_only:
            message = f"File validated successfully. {result.total_records} records found."
        elif result.status == "processing":
            message = "File uploaded successfully and is being processed in background."
        else:
            message = f"File processed successfully. {result.successful_records} records imported."

        return UploadResponse(
            upload_id=result.upload_id,
            status=result.status,
            file_name=result.file_name or file.filename,
            file_size=result.file_size or len(file_content),
            total_records=result.total_records,
            message=message
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": str(e),
                "errors": e.errors
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )


@router.post("/time-entries", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_time_entries(
    file: UploadFile = File(..., description="CSV file with time entry data"),
    validate_only: bool = Query(False, description="Only validate without saving"),
    service: UploadService = Depends(get_upload_service)
):
    """
    Upload time entries CSV file

    Accepts CSV files with time entry data for bulk import.
    Supports validation-only mode for testing file format.

    CSV Format:
    - employee_email: Employee email (must exist in system)
    - date: Work date in YYYY-MM-DD format
    - hours: Hours worked (decimal, 0.1-24.0)
    - description: Work description (minimum 10 characters)
    - billable: true/false, yes/no, or 1/0

    File Processing:
    - Files under 100 records: Processed immediately
    - Files over 100 records: Processed in background
    - Maximum file size: 10MB
    - Validates employee existence before processing

    Returns upload ID for status tracking.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('text/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a CSV file."
        )

    # Check file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10MB."
        )

    try:
        # Reset file pointer
        file_data = io.BytesIO(file_content)

        # Process upload
        result = service.upload_time_entries_csv(file_data, file.filename, validate_only)

        # Generate response message
        if validate_only:
            message = f"File validated successfully. {result.total_records} records found."
        elif result.status == "processing":
            message = "File uploaded successfully and is being processed in background."
        else:
            message = f"File processed successfully. {result.successful_records} records imported."

        return UploadResponse(
            upload_id=result.upload_id,
            status=result.status,
            file_name=result.file_name or file.filename,
            file_size=result.file_size or len(file_content),
            total_records=result.total_records,
            message=message
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": str(e),
                "errors": e.errors
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )


@router.get("/status/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    service: UploadService = Depends(get_upload_service)
):
    """
    Get upload processing status

    Returns detailed status of file upload and processing including:
    - Processing progress and completion status
    - Record counts (total, processed, successful, failed)
    - Validation errors with row and field details
    - Timestamps for tracking processing time

    Status Values:
    - pending: Upload received, not yet started
    - processing: Currently being processed
    - completed: Processing finished successfully
    - failed: Processing failed due to system error
    - validated: File structure validated (validation-only mode)

    Progress tracking available for background processing jobs.
    """
    result = service.get_upload_status(upload_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {upload_id} not found"
        )

    # Calculate progress percentage
    progress = 0.0
    if result.total_records > 0:
        progress = (result.processed_records / result.total_records) * 100

    return UploadStatusResponse(
        upload_id=result.upload_id,
        status=result.status,
        file_name=result.file_name,
        file_size=result.file_size,
        total_records=result.total_records,
        processed_records=result.processed_records,
        successful_records=result.successful_records,
        failed_records=result.failed_records,
        errors=result.errors,
        created_at=result.created_at.isoformat(),
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        progress_percentage=progress
    )


@router.get("/history", response_model=UploadHistoryResponse)
async def get_upload_history(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of uploads to return"),
    service: UploadService = Depends(get_upload_service)
):
    """
    Get upload history

    Returns list of recent uploads with their status and statistics.
    Useful for monitoring upload activity and troubleshooting failed imports.

    Results are sorted by creation date (newest first).
    Includes summary statistics for each upload.
    """
    results = service.get_upload_history(limit)

    uploads = []
    for result in results:
        # Calculate progress percentage
        progress = 0.0
        if result.total_records > 0:
            progress = (result.processed_records / result.total_records) * 100

        uploads.append(UploadStatusResponse(
            upload_id=result.upload_id,
            status=result.status,
            file_name=result.file_name,
            file_size=result.file_size,
            total_records=result.total_records,
            processed_records=result.processed_records,
            successful_records=result.successful_records,
            failed_records=result.failed_records,
            errors=result.errors,
            created_at=result.created_at.isoformat(),
            started_at=result.started_at.isoformat() if result.started_at else None,
            completed_at=result.completed_at.isoformat() if result.completed_at else None,
            progress_percentage=progress
        ))

    return UploadHistoryResponse(
        uploads=uploads,
        total_count=len(uploads)
    )


@router.get("/templates/{template_type}")
async def get_upload_template(
    template_type: str,
    service: UploadService = Depends(get_upload_service)
):
    """
    Download CSV template for uploads

    Provides CSV templates with correct column headers and example data
    for import file preparation.

    Available Templates:
    - employees: Template for employee data imports
    - time-entries: Template for time entry data imports

    Templates include:
    - Required column headers
    - Example data rows showing correct formats
    - Comments explaining field requirements

    Returns CSV file ready for download and editing.
    """
    if template_type == "employees":
        template_content = service.generate_employee_template()
        filename = "employee_import_template.csv"
    elif template_type == "time-entries":
        template_content = service.generate_time_entry_template()
        filename = "time_entry_import_template.csv"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template type: {template_type}. Available: employees, time-entries"
        )

    # Return CSV file as download
    return StreamingResponse(
        io.StringIO(template_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/files/{bucket}/{filename}")
async def download_file(
    bucket: str,
    filename: str,
    storage_service: LocalStorageService = Depends(get_storage_service)
):
    """
    Download uploaded files

    Provides secure access to uploaded files through the API.
    Supports various file types with appropriate content-type headers.

    URL-safe filename encoding supported for files with special characters.
    Access control can be added here for security (user permissions, etc.).

    Returns file content with appropriate headers for browser download.
    """
    try:
        # Get file metadata for content type
        metadata = storage_service.get_file_metadata(bucket, filename)
        content_type = metadata.get("content_type", "application/octet-stream")

        # Download file
        file_data = storage_service.download_file(bucket, filename)

        return StreamingResponse(
            file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(metadata.get("size", 0))
            }
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {bucket}/{filename}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )