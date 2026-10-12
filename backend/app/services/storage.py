"""Document storage.

A small interface so local disk storage can be swapped for S3 later without
touching callers. Files are written under backend/storage/ (gitignored).
"""
import os
import uuid
from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    def save(self, shipment_id: int, filename: str, data: bytes) -> str:
        """Persist bytes and return an opaque storage_path."""

    @abstractmethod
    def read(self, storage_path: str) -> bytes:
        ...


class LocalStorage(Storage):
    def __init__(self, root: str | None = None):
        self.root = root or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage")
        os.makedirs(self.root, exist_ok=True)

    def save(self, shipment_id: int, filename: str, data: bytes) -> str:
        safe = f"{shipment_id}/{uuid.uuid4().hex}_{os.path.basename(filename)}"
        full = os.path.join(self.root, safe)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)
        return safe  # relative path is the storage_path

    def read(self, storage_path: str) -> bytes:
        with open(os.path.join(self.root, storage_path), "rb") as f:
            return f.read()


# Default backend. Swap here (or via a factory) for S3 later.
storage: Storage = LocalStorage()
