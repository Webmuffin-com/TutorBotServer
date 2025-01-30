import boto3
from botocore.client import Config

from constants import (
    s3_bucket_endpoint,
    s3_bucket_access_key,
    s3_bucket_access_secret,
    s3_bucket_name,
    cloud_mode_enabled,
)

s3_client = (
    boto3.client(
        "s3",
        endpoint_url=s3_bucket_endpoint,
        aws_access_key_id=s3_bucket_access_key,
        aws_secret_access_key=s3_bucket_access_secret,
        config=Config(signature_version="s3v4"),
    )
    if cloud_mode_enabled
    else None
)

s3_resource = (
    boto3.resource(
        "s3",
        endpoint_url=s3_bucket_endpoint,
        aws_access_key_id=s3_bucket_access_key,
        aws_secret_access_key=s3_bucket_access_secret,
        config=Config(signature_version="s3v4"),
    )
    if cloud_mode_enabled
    else None
)

s3_bucket = s3_resource.Bucket(s3_bucket_name) if s3_resource else None  # type: ignore
