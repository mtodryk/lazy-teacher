import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings as django_settings

logger: logging.Logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self):
        self._bucket = django_settings.AWS_S3_BUCKET_NAME
        self._region = django_settings.AWS_S3_REGION_NAME

        config = Config(
            s3={"addressing_style": "virtual"},
            signature_version="s3v4",
        )

        self._client = boto3.client(
            "s3",
            aws_access_key_id=django_settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=django_settings.AWS_SECRET_ACCESS_KEY,
            region_name=self._region,
            config=config,
        )

    def upload_file(self, file_path: str, s3_key: str) -> None:
        self._client.upload_file(
            file_path,
            self._bucket,
            s3_key,
            ExtraArgs={"ContentType": "application/pdf"},
        )
        logger.info("Uploaded %s to S3 bucket %s", s3_key, self._bucket)

    def generate_presigned_url(
        self, s3_key: str, filename: str = "", expiration: int = 3600
    ) -> str:
        params: dict = {"Bucket": self._bucket, "Key": s3_key}
        if filename:
            params["ResponseContentDisposition"] = f'inline; filename="{filename}"'
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expiration,
            )
        except ClientError:
            logger.exception("Failed to generate presigned URL for %s", s3_key)
            raise

    def delete_file(self, s3_key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
            logger.info("Deleted %s from S3 bucket %s", s3_key, self._bucket)
        except ClientError:
            logger.exception("Failed to delete %s from S3", s3_key)
            raise
