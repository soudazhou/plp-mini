"""
Local File Storage Service - S3 Alternative
T052 - Local file storage service (S3 alternative)

Provides local file storage functionality as an alternative to AWS S3.
Educational focus on understanding cloud storage patterns while
maintaining local development capabilities.

AWS S3 comparison:
import boto3
s3_client = boto3.client('s3')
response = s3_client.upload_file(local_file, bucket, key)
"""

import os
import uuid
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, BinaryIO
from urllib.parse import quote

from settings import get_settings

settings = get_settings()


class LocalStorageService:
    """
    Local file storage service mimicking AWS S3 functionality.

    Educational comparison:
    - Local files: Organized in bucket-like directories
    - AWS S3: Objects in buckets with keys
    - Metadata: JSON files alongside data files
    - URLs: Local file:// URLs vs S3 signed URLs
    """

    def __init__(self, storage_root: str = None):
        """
        Initialize local storage service.

        Args:
            storage_root: Root directory for file storage.
                         Defaults to PROJECT_ROOT/storage/
        """
        self.storage_root = Path(storage_root or settings.local_storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def upload_file(self, file_data: BinaryIO, bucket: str, key: str,
                   content_type: str = None, metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload file to local storage.

        AWS S3 equivalent:
        s3_client.upload_fileobj(
            file_data,
            bucket,
            key,
            ExtraArgs={
                'ContentType': content_type,
                'Metadata': metadata or {}
            }
        )

        Args:
            file_data: File data to upload
            bucket: Bucket name (becomes directory)
            key: File key/path within bucket
            content_type: MIME type of file
            metadata: Additional file metadata

        Returns:
            Dictionary with upload result:
            - bucket: Bucket name
            - key: File key
            - size: File size in bytes
            - etag: MD5 hash of file content
            - last_modified: Upload timestamp
            - url: Local file URL
        """
        # Create bucket directory
        bucket_path = self.storage_root / bucket
        bucket_path.mkdir(parents=True, exist_ok=True)

        # Create full file path
        file_path = bucket_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate MD5 hash while writing
        md5_hash = hashlib.md5()
        file_size = 0

        # Write file data
        with open(file_path, 'wb') as f:
            for chunk in iter(lambda: file_data.read(8192), b''):
                if not chunk:
                    break
                f.write(chunk)
                md5_hash.update(chunk)
                file_size += len(chunk)

        etag = md5_hash.hexdigest()

        # Create metadata file
        metadata_info = {
            "bucket": bucket,
            "key": key,
            "size": file_size,
            "etag": etag,
            "content_type": content_type,
            "last_modified": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata_info, f, indent=2)

        return {
            "bucket": bucket,
            "key": key,
            "size": file_size,
            "etag": etag,
            "last_modified": metadata_info["last_modified"],
            "url": self._generate_file_url(bucket, key)
        }

    def download_file(self, bucket: str, key: str) -> BinaryIO:
        """
        Download file from local storage.

        AWS S3 equivalent:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body']

        Args:
            bucket: Bucket name
            key: File key

        Returns:
            File data stream

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = self.storage_root / bucket / key

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{key} not found")

        return open(file_path, 'rb')

    def delete_file(self, bucket: str, key: str) -> bool:
        """
        Delete file from local storage.

        AWS S3 equivalent:
        s3_client.delete_object(Bucket=bucket, Key=key)

        Args:
            bucket: Bucket name
            key: File key

        Returns:
            True if file was deleted, False if not found
        """
        file_path = self.storage_root / bucket / key
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')

        deleted = False

        if file_path.exists():
            file_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()

        return deleted

    def list_files(self, bucket: str, prefix: str = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        List files in bucket.

        AWS S3 equivalent:
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=limit
        )

        Args:
            bucket: Bucket name
            prefix: Key prefix filter
            limit: Maximum number of files to return

        Returns:
            List of file information dictionaries
        """
        bucket_path = self.storage_root / bucket

        if not bucket_path.exists():
            return []

        files = []
        count = 0

        for file_path in bucket_path.rglob('*'):
            if count >= limit:
                break

            # Skip metadata files and directories
            if file_path.suffix == '.meta' or file_path.is_dir():
                continue

            # Calculate relative key
            key = str(file_path.relative_to(bucket_path))

            # Apply prefix filter
            if prefix and not key.startswith(prefix):
                continue

            # Get file metadata
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
            metadata = {}

            if metadata_path.exists():
                import json
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

            # Get file stats
            stat = file_path.stat()

            files.append({
                "key": key,
                "size": metadata.get("size", stat.st_size),
                "etag": metadata.get("etag", ""),
                "last_modified": metadata.get("last_modified",
                                            datetime.fromtimestamp(stat.st_mtime).isoformat()),
                "content_type": metadata.get("content_type"),
                "url": self._generate_file_url(bucket, key)
            })

            count += 1

        return sorted(files, key=lambda x: x["last_modified"], reverse=True)

    def get_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Get file metadata without downloading content.

        AWS S3 equivalent:
        response = s3_client.head_object(Bucket=bucket, Key=key)

        Args:
            bucket: Bucket name
            key: File key

        Returns:
            File metadata dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = self.storage_root / bucket / key
        metadata_path = file_path.with_suffix(file_path.suffix + '.meta')

        if not file_path.exists():
            raise FileNotFoundError(f"File {bucket}/{key} not found")

        # Load metadata from .meta file
        metadata = {}
        if metadata_path.exists():
            import json
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Fallback to file stats if no metadata
        if not metadata:
            stat = file_path.stat()
            metadata = {
                "bucket": bucket,
                "key": key,
                "size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }

        metadata["url"] = self._generate_file_url(bucket, key)
        return metadata

    def create_bucket(self, bucket: str) -> bool:
        """
        Create bucket directory.

        AWS S3 equivalent:
        s3_client.create_bucket(Bucket=bucket)

        Args:
            bucket: Bucket name

        Returns:
            True if bucket was created, False if already exists
        """
        bucket_path = self.storage_root / bucket

        if bucket_path.exists():
            return False

        bucket_path.mkdir(parents=True, exist_ok=True)
        return True

    def delete_bucket(self, bucket: str, force: bool = False) -> bool:
        """
        Delete bucket directory.

        AWS S3 equivalent:
        s3_client.delete_bucket(Bucket=bucket)

        Args:
            bucket: Bucket name
            force: Delete non-empty bucket

        Returns:
            True if bucket was deleted

        Raises:
            ValueError: If bucket not empty and force=False
        """
        bucket_path = self.storage_root / bucket

        if not bucket_path.exists():
            return False

        # Check if bucket is empty
        if any(bucket_path.iterdir()) and not force:
            raise ValueError(f"Bucket '{bucket}' is not empty. Use force=True to delete.")

        shutil.rmtree(bucket_path)
        return True

    def list_buckets(self) -> List[str]:
        """
        List all buckets.

        AWS S3 equivalent:
        response = s3_client.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets']]

        Returns:
            List of bucket names
        """
        if not self.storage_root.exists():
            return []

        return [item.name for item in self.storage_root.iterdir() if item.is_dir()]

    def _generate_file_url(self, bucket: str, key: str) -> str:
        """
        Generate local file URL.

        AWS S3 equivalent would generate signed URLs:
        s3_client.generate_presigned_url('get_object',
                                        Params={'Bucket': bucket, 'Key': key})

        Args:
            bucket: Bucket name
            key: File key

        Returns:
            Local file URL
        """
        # For local development, return a URL that can be served by the API
        encoded_key = quote(key, safe='/')
        return f"/api/v1/files/{bucket}/{encoded_key}"

    def get_file_path(self, bucket: str, key: str) -> Path:
        """
        Get absolute file path for direct file system access.

        Note: This method is specific to local storage and wouldn't exist in S3.
        Useful for cases where direct file access is needed.

        Args:
            bucket: Bucket name
            key: File key

        Returns:
            Absolute path to file
        """
        return self.storage_root / bucket / key

    def copy_file(self, source_bucket: str, source_key: str,
                 dest_bucket: str, dest_key: str) -> Dict[str, Any]:
        """
        Copy file within local storage.

        AWS S3 equivalent:
        s3_client.copy_object(
            CopySource={'Bucket': source_bucket, 'Key': source_key},
            Bucket=dest_bucket,
            Key=dest_key
        )

        Args:
            source_bucket: Source bucket name
            source_key: Source file key
            dest_bucket: Destination bucket name
            dest_key: Destination file key

        Returns:
            Copy result dictionary

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        source_path = self.storage_root / source_bucket / source_key

        if not source_path.exists():
            raise FileNotFoundError(f"Source file {source_bucket}/{source_key} not found")

        # Create destination bucket
        dest_bucket_path = self.storage_root / dest_bucket
        dest_bucket_path.mkdir(parents=True, exist_ok=True)

        # Copy file
        dest_path = dest_bucket_path / dest_key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)

        # Copy metadata
        source_meta = source_path.with_suffix(source_path.suffix + '.meta')
        if source_meta.exists():
            dest_meta = dest_path.with_suffix(dest_path.suffix + '.meta')
            shutil.copy2(source_meta, dest_meta)

            # Update metadata
            import json
            with open(dest_meta, 'r+') as f:
                metadata = json.load(f)
                metadata['bucket'] = dest_bucket
                metadata['key'] = dest_key
                f.seek(0)
                json.dump(metadata, f, indent=2)
                f.truncate()

        return {
            "source_bucket": source_bucket,
            "source_key": source_key,
            "dest_bucket": dest_bucket,
            "dest_key": dest_key,
            "url": self._generate_file_url(dest_bucket, dest_key)
        }


# Global storage service instance
_storage_service: Optional[LocalStorageService] = None


def get_storage_service() -> LocalStorageService:
    """Get the global storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = LocalStorageService()
    return _storage_service


# Educational Notes: Local Storage vs AWS S3
#
# 1. API Compatibility:
#    - Method signatures mirror S3 SDK
#    - Return values match S3 response structure
#    - Error handling follows S3 patterns
#
# 2. Metadata Management:
#    - S3: Built-in metadata support
#    - Local: .meta files store additional information
#    - Content-Type, ETag, custom metadata preserved
#
# 3. URL Generation:
#    - S3: Signed URLs for temporary access
#    - Local: API endpoints serve files
#    - Both provide secure, controlled access
#
# 4. File Organization:
#    - S3: Flat namespace with key prefixes
#    - Local: Directory structure mirrors key paths
#    - Bucket concept preserved in both
#
# 5. Migration Path:
#    - Service interface remains consistent
#    - Can swap implementations without API changes
#    - Environment variables control storage backend