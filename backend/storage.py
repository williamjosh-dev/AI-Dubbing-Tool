import mimetypes
import os
import uuid
from pathlib import Path

import boto3
from supabase import Client, create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "dubbing-files")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")


def get_storage_client() -> Client:
    """Create a server-side client for Storage operations."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def download_r2_file(object_key: str, destination: Path) -> None:
    """Download an input uploaded through the browser's R2 presigned URL."""
    if not all((R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME)):
        raise RuntimeError(
            "R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and "
            "R2_BUCKET_NAME must be configured."
        )
    if not object_key.startswith("uploads/") or ".." in Path(object_key).parts:
        raise ValueError("Invalid R2 object key.")

    client = boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(R2_BUCKET_NAME, object_key, str(destination))


def upload_r2_file(file_path: Path, job_id: str, file_kind: str) -> str:
    """Upload a generated result to R2 and return a temporary download URL."""
    if not all((R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME)):
        raise RuntimeError("R2 storage is not fully configured.")
    if not file_path.is_file():
        raise FileNotFoundError(f"Storage upload file does not exist: {file_path}")

    client = boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )
    object_key = f"outputs/{job_id}/{file_kind}{file_path.suffix.lower()}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    client.upload_file(
        str(file_path),
        R2_BUCKET_NAME,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": R2_BUCKET_NAME, "Key": object_key},
        ExpiresIn=7 * 24 * 60 * 60,
    )


def upload_public_file(file_path: Path, job_id: str, file_kind: str) -> str:
    """Upload a file under an unguessable path and return its public URL."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Storage upload file does not exist: {file_path}")

    object_name = f"{uuid.uuid4().hex}{file_path.suffix.lower()}"
    object_path = f"jobs/{job_id}/{file_kind}/{object_name}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    client = get_storage_client()

    with file_path.open("rb") as file_handle:
        client.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            object_path,
            file_handle,
            {"content-type": content_type, "upsert": "false"},
        )

    return client.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(object_path)