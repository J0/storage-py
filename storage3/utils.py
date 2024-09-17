import json
import os
import tempfile

from datetime import datetime
from hashlib import md5

from httpx import AsyncClient as AsyncClient  # noqa: F401
from httpx import Client as BaseClient

from .types import FileInfo


class SyncClient(BaseClient):
    def aclose(self) -> None:
        self.close()


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""


class FileStore:
    """This class serves as storage of files to be sent in the resumable upload workflow"""

    def __init__(self):
        self.storage = {}
        self.disk_storage = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
        self.reload_storage()

    def fingerprint(self, file_info: FileInfo):
        """Generates a fingerprint based on the content of the file being sent"""

        block_size = 64 * 1024
        min_size = min(block_size, int(file_info["length"]))

        with open(file_info["name"], "rb") as f:
            data = f.read(min_size)
            file_info["fingerprint"] = md5(data).hexdigest()

    def persist(self):
        with open(self.disk_storage.name, 'w') as f:
            f.seek(0)
            f.write(json.dumps(self.storage))
            f.flush()

    def mark_file(self, file_info: FileInfo):
        """Store file metadata in a in-memory storage"""

        if len(file_info["length"]) != 0:
            self.fingerprint(file_info)
            file_info["mtime"] = os.stat(file_info["name"]).st_mtime

        self.storage[file_info["name"]] = file_info
        self.persist()

    def get_file_info(self, filename):
        self.reload_storage()
        return self.storage[filename]

    def reload_storage(self):
        self.storage = {}
        size = os.stat(self.disk_storage.name).st_size
        if size > 0:
            with open(self.disk_storage.name) as f:
                self.storage = json.load(f)

    def update_file_headers(self, filename, key, value):
        file = self.get_file_info(filename)
        is_link_expired = file["expiration_time"] < datetime.now().timestamp()

        if not is_link_expired:
            file["headers"][key] = value
            self.storage[filename] = file
            self.persist()
        else:
            self.remove_file(filename)
            raise StorageException("Upload link is expired")

    def delete_file_headers(self, filename, key):
        file = self.get_file_info(filename)
        if key in file["headers"]:
            del file["headers"][key]
            self.storage[filename] = file
            self.persist()

    def get_file_headers(self, filename):
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
        file.seek(int(offset))
        return file

    def close_file(self, filename):
        filename.close()

    def remove_file(self, filename: str):
        del self.storage[filename]
        self.persist()

    def get_link(self, filename: str):
        return self.storage[filename]["link"]
