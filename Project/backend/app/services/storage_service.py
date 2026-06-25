import io
import os
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.config import settings


class StorageService:
    def __init__(self) -> None:
        self.use_local = settings.USE_LOCAL_STORAGE or not settings.AWS_ACCESS_KEY_ID
        if not self.use_local:
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
        else:
            Path(settings.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    async def upload(self, content: bytes, filename: str, content_type: str) -> str:
        ext = Path(filename).suffix
        key = f"documents/{uuid.uuid4().hex}{ext}"

        if self.use_local:
            path = Path(settings.LOCAL_STORAGE_PATH) / key.replace("/", os.sep)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            return key

        self.s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return key

    async def download(self, key: str) -> bytes:
        if self.use_local:
            path = Path(settings.LOCAL_STORAGE_PATH) / key.replace("/", os.sep)
            return path.read_bytes()

        buffer = io.BytesIO()
        self.s3.download_fileobj(settings.S3_BUCKET, key, buffer)
        return buffer.getvalue()

    def get_url(self, key: str) -> str:
        if self.use_local:
            return f"/uploads/{key}"
        return f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


storage_service = StorageService()
