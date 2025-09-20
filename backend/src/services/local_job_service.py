"""
Local Job Processing Service - Celery/SQS Alternative
T053 - Local job processing service (Celery/SQS alternative)

Provides local job queue functionality as an alternative to AWS SQS + Celery.
Educational focus on understanding distributed task processing patterns while
maintaining local development capabilities.

AWS SQS + Celery comparison:
import boto3
sqs = boto3.client('sqs')
sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(task_data))

from celery import Celery
app = Celery('tasks')
@app.task
def process_document(document_id):
    # Process document
    pass
"""

import os
import json
import uuid
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from queue import Queue, Empty
from pathlib import Path
from enum import Enum
import pickle
import logging

from settings import get_settings

settings = get_settings()


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class Job:
    """
    Job representation for task processing

    AWS SQS Message equivalent:
    {
        "MessageId": "uuid",
        "Body": "json_task_data",
        "Attributes": {
            "ApproximateReceiveCount": "1",
            "SentTimestamp": "timestamp"
        }
    }
    """

    def __init__(self, task_name: str, task_data: Dict[str, Any],
                 priority: JobPriority = JobPriority.NORMAL,
                 retry_count: int = 3, delay: int = 0):
        self.id = str(uuid.uuid4())
        self.task_name = task_name
        self.task_data = task_data
        self.priority = priority
        self.status = JobStatus.PENDING
        self.retry_count = retry_count
        self.max_retries = retry_count
        self.delay = delay
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization"""
        return {
            "id": self.id,
            "task_name": self.task_name,
            "task_data": self.task_data,
            "priority": self.priority.value,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "delay": self.delay,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "result": self.result
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary"""
        job = cls(
            task_name=data["task_name"],
            task_data=data["task_data"],
            priority=JobPriority(data["priority"]),
            retry_count=data["retry_count"]
        )
        job.id = data["id"]
        job.status = JobStatus(data["status"])
        job.max_retries = data["max_retries"]
        job.delay = data["delay"]
        job.created_at = datetime.fromisoformat(data["created_at"])
        job.started_at = datetime.fromisoformat(data["started_at"]) if data["started_at"] else None
        job.completed_at = datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None
        job.error_message = data["error_message"]
        job.result = data["result"]
        return job


class LocalJobService:
    """
    Local job processing service mimicking Celery + SQS functionality.

    Educational comparison:
    - Local queues: In-memory with disk persistence
    - AWS SQS: Managed message queues
    - Celery: Distributed task processing
    - Workers: Thread-based vs process-based
    - Persistence: JSON files vs cloud storage
    """

    def __init__(self, storage_root: str = None, max_workers: int = 4):
        """
        Initialize local job service.

        Args:
            storage_root: Root directory for job persistence
            max_workers: Maximum number of worker threads
        """
        self.storage_root = Path(storage_root or settings.local_storage_root) / "jobs"
        self.storage_root.mkdir(parents=True, exist_ok=True)

        self.max_workers = max_workers
        self.workers: List[threading.Thread] = []
        self.running = False

        # Job queues by priority
        self.queues: Dict[JobPriority, Queue] = {
            priority: Queue() for priority in JobPriority
        }

        # Job registry
        self.jobs: Dict[str, Job] = {}
        self.task_handlers: Dict[str, Callable] = {}

        # Load persisted jobs
        self._load_jobs()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def register_task(self, task_name: str, handler: Callable) -> None:
        """
        Register a task handler function.

        Celery equivalent:
        @app.task
        def process_document(document_id):
            return document_processor.process(document_id)

        Args:
            task_name: Name of the task
            handler: Function to handle the task
        """
        self.task_handlers[task_name] = handler
        self.logger.info(f"Registered task handler: {task_name}")

    def enqueue_job(self, task_name: str, task_data: Dict[str, Any],
                   priority: JobPriority = JobPriority.NORMAL,
                   retry_count: int = 3, delay: int = 0) -> str:
        """
        Enqueue a job for processing.

        AWS SQS equivalent:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(task_data),
            MessageAttributes={
                'task_name': {'StringValue': task_name},
                'priority': {'StringValue': str(priority)}
            }
        )

        Args:
            task_name: Name of the task to execute
            task_data: Data to pass to the task
            priority: Job priority level
            retry_count: Number of retry attempts
            delay: Delay before processing (seconds)

        Returns:
            Job ID for tracking
        """
        if task_name not in self.task_handlers:
            raise ValueError(f"Unknown task: {task_name}")

        job = Job(
            task_name=task_name,
            task_data=task_data,
            priority=priority,
            retry_count=retry_count,
            delay=delay
        )

        self.jobs[job.id] = job

        # Add to appropriate priority queue
        self.queues[priority].put(job)

        # Persist job
        self._save_job(job)

        self.logger.info(f"Enqueued job {job.id}: {task_name}")
        return job.id

    def start_workers(self) -> None:
        """
        Start worker threads to process jobs.

        Celery equivalent:
        celery -A tasks worker --loglevel=info --concurrency=4
        """
        if self.running:
            return

        self.running = True

        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"JobWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        self.logger.info(f"Started {self.max_workers} job workers")

    def stop_workers(self) -> None:
        """Stop all worker threads"""
        self.running = False

        # Signal all workers to stop
        for priority in JobPriority:
            for _ in range(self.max_workers):
                self.queues[priority].put(None)  # Poison pill

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5.0)

        self.workers.clear()
        self.logger.info("Stopped all job workers")

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status and details.

        Args:
            job_id: Job identifier

        Returns:
            Job status dictionary or None if not found
        """
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None

    def list_jobs(self, status: Optional[JobStatus] = None,
                 task_name: Optional[str] = None,
                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        List jobs with optional filtering.

        Args:
            status: Filter by job status
            task_name: Filter by task name
            limit: Maximum number of jobs to return

        Returns:
            List of job dictionaries
        """
        jobs = list(self.jobs.values())

        # Apply filters
        if status:
            jobs = [job for job in jobs if job.status == status]

        if task_name:
            jobs = [job for job in jobs if job.task_name == task_name]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return [job.to_dict() for job in jobs[:limit]]

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was cancelled, False otherwise
        """
        job = self.jobs.get(job_id)
        if not job or job.status != JobStatus.PENDING:
            return False

        job.status = JobStatus.FAILED
        job.error_message = "Job cancelled by user"
        job.completed_at = datetime.utcnow()

        self._save_job(job)
        return True

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue stats
        """
        stats = {
            "total_jobs": len(self.jobs),
            "queue_sizes": {
                priority.name: self.queues[priority].qsize()
                for priority in JobPriority
            },
            "status_counts": {},
            "registered_tasks": list(self.task_handlers.keys()),
            "workers_running": len(self.workers),
            "service_running": self.running
        }

        # Count jobs by status
        for status in JobStatus:
            count = sum(1 for job in self.jobs.values() if job.status == status)
            stats["status_counts"][status.name] = count

        return stats

    def _worker_loop(self) -> None:
        """Main worker loop for processing jobs"""
        worker_name = threading.current_thread().name
        self.logger.info(f"Worker {worker_name} started")

        while self.running:
            job = self._get_next_job()

            if job is None:  # Poison pill or timeout
                continue

            self._process_job(job)

        self.logger.info(f"Worker {worker_name} stopped")

    def _get_next_job(self) -> Optional[Job]:
        """Get next job from priority queues"""
        # Check queues in priority order (URGENT -> LOW)
        for priority in sorted(JobPriority, key=lambda p: p.value, reverse=True):
            try:
                job = self.queues[priority].get(timeout=1.0)
                if job is None:  # Poison pill
                    return None
                return job
            except Empty:
                continue

        return None

    def _process_job(self, job: Job) -> None:
        """Process a single job"""
        # Check if job should be delayed
        if job.delay > 0:
            time.sleep(job.delay)
            job.delay = 0  # Clear delay after first execution

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        self._save_job(job)

        self.logger.info(f"Processing job {job.id}: {job.task_name}")

        try:
            handler = self.task_handlers[job.task_name]
            result = handler(**job.task_data)

            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()

            self.logger.info(f"Job {job.id} completed successfully")

        except Exception as e:
            self.logger.error(f"Job {job.id} failed: {e}")

            job.error_message = str(e)
            job.retry_count -= 1

            if job.retry_count > 0:
                job.status = JobStatus.RETRYING
                # Re-queue with exponential backoff
                job.delay = min(60, 2 ** (job.max_retries - job.retry_count))
                self.queues[job.priority].put(job)
                self.logger.info(f"Job {job.id} will retry in {job.delay} seconds")
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()
                self.logger.error(f"Job {job.id} failed permanently")

        self._save_job(job)

    def _save_job(self, job: Job) -> None:
        """Persist job to disk"""
        job_file = self.storage_root / f"{job.id}.json"
        with open(job_file, 'w') as f:
            json.dump(job.to_dict(), f, indent=2)

    def _load_jobs(self) -> None:
        """Load persisted jobs from disk"""
        if not self.storage_root.exists():
            return

        for job_file in self.storage_root.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    job_data = json.load(f)

                job = Job.from_dict(job_data)
                self.jobs[job.id] = job

                # Re-queue pending jobs
                if job.status == JobStatus.PENDING:
                    self.queues[job.priority].put(job)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.warning(f"Failed to load job from {job_file}: {e}")

    def cleanup_old_jobs(self, max_age_days: int = 30) -> int:
        """
        Clean up old completed/failed jobs.

        Args:
            max_age_days: Maximum age of jobs to keep

        Returns:
            Number of jobs cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned_count = 0

        for job_id, job in list(self.jobs.items()):
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED] and
                job.completed_at and job.completed_at < cutoff_date):

                # Remove from memory
                del self.jobs[job_id]

                # Remove from disk
                job_file = self.storage_root / f"{job_id}.json"
                if job_file.exists():
                    job_file.unlink()

                cleaned_count += 1

        self.logger.info(f"Cleaned up {cleaned_count} old jobs")
        return cleaned_count


# Global job service instance
_job_service: Optional[LocalJobService] = None


def get_job_service() -> LocalJobService:
    """Get the global job service instance"""
    global _job_service
    if _job_service is None:
        _job_service = LocalJobService()
        _job_service.start_workers()
    return _job_service


# Educational Notes: Local Job Processing vs Celery + SQS
#
# 1. Task Registration:
#    - Celery: @app.task decorator
#    - Local: register_task() method
#    - Both provide function-based task definition
#
# 2. Job Queuing:
#    - SQS: send_message() with JSON payload
#    - Local: enqueue_job() with structured data
#    - Priority queues vs single SQS queue
#
# 3. Worker Management:
#    - Celery: Separate worker processes
#    - Local: Thread-based workers
#    - Both support horizontal scaling
#
# 4. Persistence:
#    - SQS: Cloud-based message persistence
#    - Local: JSON file storage
#    - Both ensure job durability
#
# 5. Retry Logic:
#    - Celery: Built-in retry decorators
#    - Local: Custom retry with exponential backoff
#    - Both support configurable retry attempts
#
# 6. Monitoring:
#    - Celery: Flower web interface
#    - Local: API endpoints for statistics
#    - Both provide job status tracking