from __future__ import annotations

import boto3

from .base import StorageBackend


class S3Storage(StorageBackend):
    def __init__(self, bucket: str, prefix: str = "chunks/", **client_kwargs) -> None:
        self.bucket = bucket
        self.prefix = prefix
        self.client = boto3.client("s3", **client_kwargs)

    def _key(self, chunk_hash: str) -> str:
        return f"{self.prefix}{chunk_hash}"

    def has_chunk(self, chunk_hash: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(chunk_hash))
            return True
        except self.client.exceptions.NoSuchKey:
            return False
        except self.client.exceptions.ClientError:
            return False

    def write_chunk(self, chunk_hash: str, data: bytes) -> None:
        if not self.has_chunk(chunk_hash):
            self.client.put_object(Bucket=self.bucket, Key=self._key(chunk_hash), Body=data)

    def read_chunk(self, chunk_hash: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=self._key(chunk_hash))
        return response["Body"].read()


__all__ = ["S3Storage"]
