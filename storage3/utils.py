import json
import os
import tempfile
from base64 import b64encode
from datetime import datetime
from hashlib import md5
from typing import Dict

from httpx import AsyncClient as AsyncClient  # noqa: F401
from httpx import Client as BaseClient

from .types import FileInfo, UploadMetadata


class SyncClient(BaseClient):
    def aclose(self) -> None:
        self.close()


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""


class FileStore:
    """This class serves as storage of files to be sent in the resumable upload workflow"""

    def __init__(self):
        self.disk_storage = tempfile.NamedTemporaryFile(mode="w+t", delete=False)
        self.reload_storage()

    def fingerprint(self, file_info: FileInfo):
        """Generates a fingerprint based on the content of the file being sent"""

        block_size = 64 * 1024
        min_size = min(block_size, int(file_info["length"]))

        with open(file_info["name"], "rb") as f:
            data = f.read(min_size)
            file_info["fingerprint"] = md5(data).hexdigest()

    def persist(self) -> None:
        """Save the current state of in-memory storage to disk"""
        with open(self.disk_storage.name, "w") as f:
            f.seek(0)
            f.write(json.dumps(self.storage, indent=2))
            f.flush()

    def mark_file(self, file_info: FileInfo):
        """Store file metadata in a in-memory storage"""

        if len(file_info["length"]) != 0:
            self.fingerprint(file_info)
            file_info["mtime"] = os.stat(file_info["name"]).st_mtime

        self.storage[file_info["name"]] = file_info
        self.persist()

    def reload_storage(self) -> None:
        """Refresh the in-memory storage"""
        self.storage = {}
        size = os.stat(self.disk_storage.name).st_size
        if size > 0:
            with open(self.disk_storage.name) as f:
                self.storage = json.load(f)

    def file_exists(self, filename: str) -> bool:
        """Verify if the file exists in the storage

        Parameters
        ----------
        filename
            This could be the local filename or objectname in the storage
        """
        self.reload_storage()
        return filename in self.storage

    def get_file_info(self, filename) -> FileInfo:
        """Returns the file info metadata associated with a filename in the storage

        Parameters
        ----------
        filename
            key name referencing to filename attributes.
        """
        if not self.file_exists(filename):
            raise StorageException(f"There is no entry for {filename} in FileStore")

        return self.storage[filename]

    def update_file_headers(self, filename, key, value) -> None:
        """Update key values from the file info metadata

        Parameters
        ----------
        filename
            key name referencing to filename attributes.
        key
            key name referencing to header attribute to be modified
        value
            new value
        """
        file = self.get_file_info(filename)
        is_link_expired = file["expiration_time"] < datetime.now().timestamp()

        if not is_link_expired:
            file["headers"][key] = value
            self.storage[filename] = file
            self.persist()
        else:
            self.remove_file(filename)
            raise StorageException("Upload link is expired")

    def delete_file_headers(self, filename, key) -> None:
        """Remove keys from the file info metadata

        Parameters
        ----------
        filename
            key name referencing to filename attributes.
        key
            key name referencing to header attribute to be removed
        """
        file = self.get_file_info(filename)
        if key in file["headers"]:
            del file["headers"][key]
            self.storage[filename] = file
            self.persist()

    def get_file_headers(self, filename) -> Dict[str, str]:
        """Returns the file's headers used during the upload workflow

        Parameters
        ----------
        filename
            key name referencing to filename attributes.
        """
        return self.get_file_info(filename)["headers"]

    def open_file(self, filename: str, offset: int):
        """Open file in the specified offset

        Parameters
        ----------
        filename
            local file
        offset
            set current the file-pointer
        """
        file = open(filename, "rb")
        file.seek(offset)
        return file

    def close_file(self, filename) -> None:
        """Close the file.

        Parameters
        ----------
        filename
            key name referencing to filename attributes.
        """
        filename.close()

    def remove_file(self, filename: str) -> None:
        """Remove filename entry in the in-memory storage and then commit the changes into the disk storage

        Parameters
        ----------
        filename
            key name referencing to filename attributes.
        """

        if not self.file_exists(filename):
            raise StorageException(f"There is no entry for {filename} in FileStore")

        del self.storage[filename]
        self.persist()

    def get_link(self, filename: str) -> str:
        """Returns the filename's link associated with its resumable endpoint

        Parameters
        ----------
        filename
            key name referencing to filename attributes.
        """

        if not self.file_exists(filename):
            raise StorageException(f"There is no entry for {filename} in FileStore")

        return self.storage[filename]["link"]

    def link_exists(self, link: str) -> bool:
        """Check if the link is already in the storage

        Parameters
        ----------
        link:
            link associated with a resumable endpoint
        """
        return any(self.get_link(obj) == link for obj in self.storage.keys())


def is_valid_arg(target: str) -> bool:
    return target is not None and isinstance(target, str) and len(target.strip()) != 0


def base64encode_metadata(metadata: UploadMetadata) -> str:
    """Generate base64 encoding for Upload-Metadata header

    Parameters
    ----------
    metadata
        Bucket and object pair representing the resulting file in the storage
    """
    res = [f"{k} {b64encode(bytes(v, 'utf-8')).decode()}" for k, v in metadata.items()]
    return ",".join(res)
