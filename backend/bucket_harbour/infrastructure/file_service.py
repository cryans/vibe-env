import os
import boto3
import hashlib
import logging
from typing import BinaryIO, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

S3_BUCKET = os.environ.get("S3_BUCKET", "belikai-file-facade")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")

class FileService:
    def __init__(self):
        # Allow bypassing real S3 for local testing via endpoint url overrides if necessary
        endpoint_url = os.environ.get("S3_ENDPOINT_URL")
        self.s3 = boto3.client("s3", region_name=S3_REGION, endpoint_url=endpoint_url)
        self.staging_dir = os.path.abspath(os.environ.get("STAGING_DIR", "/tmp/belikai_staging"))
        os.makedirs(self.staging_dir, exist_ok=True)

        # Automatically ensure the bucket exists when using a custom endpoint url (like MinIO)
        if endpoint_url:
            try:
                self.s3.head_bucket(Bucket=S3_BUCKET)
                logger.info(f"S3 bucket '{S3_BUCKET}' verified on startup.")
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                if error_code in ('404', '403'): # 404 Not Found or 403 Forbidden (can indicate bucket doesn't exist/access issue)
                    try:
                        logger.info(f"S3 bucket '{S3_BUCKET}' not found or inaccessible. Attempting to create it...")
                        self.s3.create_bucket(Bucket=S3_BUCKET)
                        logger.info(f"S3 bucket '{S3_BUCKET}' successfully created.")
                    except Exception as create_err:
                        logger.warning(f"Could not automatically create bucket '{S3_BUCKET}': {create_err}")
                else:
                    logger.warning(f"head_bucket check failed with code {error_code}: {e}")
            except Exception as e:
                logger.warning(f"Could not verify or create bucket '{S3_BUCKET}': {e}")

    def save_to_staging(self, file_id: str, file_stream: BinaryIO) -> tuple[str, str]:
        filepath = os.path.join(self.staging_dir, file_id)
        hasher = hashlib.sha256()
        with open(filepath, "wb") as f:
            for chunk in iter(lambda: file_stream.read(8192), b""):
                f.write(chunk)
                hasher.update(chunk)
        return filepath, hasher.hexdigest()

    def get_staged_filepath(self, file_id: str) -> str:
        return os.path.join(self.staging_dir, file_id)

    def _calculate_checksum(self, filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def upload_to_s3(self, file_id: str, checksum: Optional[str] = None) -> str:
        filepath = self.get_staged_filepath(file_id)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Staged file not found: {file_id}")
            
        if checksum is None:
            checksum = self._calculate_checksum(filepath)
        s3_key = file_id
        
        self.s3.upload_file(
            filepath,
            S3_BUCKET,
            s3_key,
            ExtraArgs={"Metadata": {"checksum": checksum}}
        )
        return checksum
        
    def generate_presigned_url(self, file_id: str) -> str:
        try:
            return self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': file_id},
                ExpiresIn=3600
            )
        except ClientError as e:
            # Handle S3 errors
            raise e
