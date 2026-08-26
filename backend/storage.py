import mimetypes
import os
import uuid
from pathlib import Path

from supabase import Client, create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "dubbing-files")


def get_storage_client() -> Client:
    """Create a server-side client for Storage operations."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


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