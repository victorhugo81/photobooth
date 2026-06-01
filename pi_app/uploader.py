import json
import logging
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

_DATA_PREFIX     = "data/"
_PHOTOS_JSON_KEY = f"{_DATA_PREFIX}photos.json"


def upload_data_file(filename: str, content: bytes) -> None:
    """Upload a settings JSON file to R2 under data/<filename>."""
    bucket = os.environ["R2_BUCKET_NAME"]
    try:
        _s3_client().put_object(
            Bucket=bucket,
            Key=f"{_DATA_PREFIX}{filename}",
            Body=content,
            ContentType="application/json",
            CacheControl="no-cache, no-store",
        )
        logger.info("Synced data/%s to R2", filename)
    except (BotoCoreError, ClientError):
        logger.warning("Failed to upload data/%s to R2", filename, exc_info=True)


def download_data_file(filename: str) -> bytes | None:
    """Download a settings JSON file from R2. Returns None if not found."""
    bucket = os.environ["R2_BUCKET_NAME"]
    try:
        resp = _s3_client().get_object(Bucket=bucket, Key=f"{_DATA_PREFIX}{filename}")
        return resp["Body"].read()
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        logger.warning("Failed to download data/%s from R2", filename, exc_info=True)
        return None
    except (BotoCoreError, Exception):
        logger.warning("Failed to download data/%s from R2", filename, exc_info=True)
        return None


def _s3_client():
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def upload_photo(local_path: str, r2_key: str) -> str:
    """Upload a JPEG file to R2. Returns the public URL."""
    bucket = os.environ["R2_BUCKET_NAME"]
    r2_public_url = os.environ["R2_PUBLIC_URL"].rstrip("/")

    try:
        client = _s3_client()
        client.upload_file(
            local_path,
            bucket,
            r2_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        public_url = f"{r2_public_url}/{r2_key}"
        logger.info("Uploaded %s → %s", r2_key, public_url)
        return public_url
    except (BotoCoreError, ClientError) as exc:
        logger.exception("R2 upload failed for %s", r2_key)
        raise RuntimeError(f"Upload failed: {exc}") from exc


def update_photos_json(filename: str, local_path: str | None = None) -> None:
    """Fetch photos.json from R2, prepend the new filename, re-upload it,
    and optionally write a local copy to *local_path*."""
    bucket = os.environ["R2_BUCKET_NAME"]
    client = _s3_client()

    try:
        resp = client.get_object(Bucket=bucket, Key=_PHOTOS_JSON_KEY)
        photos: list = json.loads(resp["Body"].read().decode("utf-8"))
        if not isinstance(photos, list):
            photos = []
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
            photos = []
        else:
            logger.exception("Failed to fetch %s", _PHOTOS_JSON_KEY)
            raise
    except json.JSONDecodeError:
        logger.warning("%s was malformed — starting fresh", _PHOTOS_JSON_KEY)
        photos = []

    photos.insert(0, filename)

    body = json.dumps(photos, indent=2).encode("utf-8")
    client.put_object(
        Bucket=bucket,
        Key=_PHOTOS_JSON_KEY,
        Body=body,
        ContentType="application/json",
        CacheControl="no-cache, no-store",
    )
    logger.info("photos.json updated (%d entries)", len(photos))

    if local_path:
        try:
            import pathlib
            pathlib.Path(local_path).write_bytes(body)
            logger.info("photos.json written locally to %s", local_path)
        except Exception:
            logger.warning("Failed to write local photos.json", exc_info=True)
