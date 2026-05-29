import logging
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


def _s3_client():
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def upload_photo(local_path: str, filename: str) -> str:
    """Upload a JPEG file to R2. Returns the public URL."""
    bucket = os.environ["R2_BUCKET_NAME"]
    r2_public_url = os.environ["R2_PUBLIC_URL"].rstrip("/")

    try:
        client = _s3_client()
        client.upload_file(
            local_path,
            bucket,
            filename,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        public_url = f"{r2_public_url}/{filename}"
        logger.info("Uploaded %s → %s", filename, public_url)
        return public_url
    except (BotoCoreError, ClientError) as exc:
        logger.exception("R2 upload failed for %s", filename)
        raise RuntimeError(f"Upload failed: {exc}") from exc
