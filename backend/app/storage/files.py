import boto3

from .. import config


def _r2():
    return boto3.client(
        "s3", endpoint_url=config.R2_ENDPOINT, region_name="auto",
        aws_access_key_id=config.R2_ACCESS_KEY_ID, aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
    )


def save(key: str, content: bytes) -> None:
    if config.R2_ENDPOINT:
        _r2().put_object(Bucket=config.R2_BUCKET, Key=key, Body=content)
        return
    path = config.FILES_DIR / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def delete(key: str) -> None:
    if config.R2_ENDPOINT:
        _r2().delete_object(Bucket=config.R2_BUCKET, Key=key)
        return
    (config.FILES_DIR / key).unlink(missing_ok=True)
