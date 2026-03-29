import pytest
from unittest.mock import patch, MagicMock

from documents.services.s3_client import S3Client


class TestS3Client:

    @pytest.fixture
    def mock_settings(self, mocker):
        mocker.patch(
            "documents.services.s3_client.django_settings.AWS_S3_BUCKET_NAME",
            "test-bucket",
        )
        mocker.patch(
            "documents.services.s3_client.django_settings.AWS_S3_REGION_NAME",
            "eu-central-1",
        )
        mocker.patch(
            "documents.services.s3_client.django_settings.AWS_ACCESS_KEY_ID", "test-key"
        )
        mocker.patch(
            "documents.services.s3_client.django_settings.AWS_SECRET_ACCESS_KEY",
            "test-secret",
        )

    @pytest.fixture
    def mock_boto3(self, mocker):
        return mocker.patch("documents.services.s3_client.boto3")

    @pytest.fixture
    def s3_client(self, mock_settings, mock_boto3):
        return S3Client()

    def test_init(self, s3_client):
        assert s3_client._bucket == "test-bucket"
        assert s3_client._region == "eu-central-1"

    def test_upload_file(self, s3_client):
        s3_client.upload_file("/tmp/test.pdf", "documents/1/1.pdf")
        s3_client._client.upload_file.assert_called_once_with(
            "/tmp/test.pdf",
            "test-bucket",
            "documents/1/1.pdf",
            ExtraArgs={"ContentType": "application/pdf"},
        )

    def test_generate_presigned_url(self, s3_client):
        s3_client._client.generate_presigned_url.return_value = "https://presigned-url"

        url = s3_client.generate_presigned_url(
            "key", filename="doc.pdf", expiration=3600
        )
        assert url == "https://presigned-url"
        call_args = s3_client._client.generate_presigned_url.call_args
        assert call_args[0][0] == "get_object"
        params = call_args[1]["Params"]
        assert params["Bucket"] == "test-bucket"
        assert params["Key"] == "key"
        assert "ResponseContentDisposition" in params

    def test_generate_presigned_url_no_filename(self, s3_client):
        s3_client._client.generate_presigned_url.return_value = "https://url"

        s3_client.generate_presigned_url("key")
        params = s3_client._client.generate_presigned_url.call_args[1]["Params"]
        assert "ResponseContentDisposition" not in params

    def test_generate_presigned_url_error(self, s3_client):
        from botocore.exceptions import ClientError

        s3_client._client.generate_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}}, "GetObject"
        )

        with pytest.raises(ClientError):
            s3_client.generate_presigned_url("key")

    def test_delete_file(self, s3_client):
        s3_client.delete_file("documents/1/1.pdf")
        s3_client._client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="documents/1/1.pdf"
        )

    def test_delete_file_error(self, s3_client):
        from botocore.exceptions import ClientError

        s3_client._client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Error"}}, "DeleteObject"
        )

        with pytest.raises(ClientError):
            s3_client.delete_file("key")
