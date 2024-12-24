import os

from conftest import is_https_url

from storage3.utils import StorageException


def test_non_valid_resumable_options(sync_client):
    client = sync_client

    """Raise an exception when argument is not a string"""
    try:
        client.resumable.resumable_offset(1, {})
    except Exception as e:
        assert isinstance(e, StorageException)

    """Raise an exception when argument is an empty string"""
    try:
        client.resumable.resumable_offset("https://random_bucket_id_link", {})
    except Exception as e:
        assert isinstance(e, StorageException)


def test_non_valid_terminate_options(sync_client):
    client = sync_client

    """Raise an exception when argument is not a string"""
    try:
        client.resumable.terminate(1)
    except Exception as e:
        assert isinstance(e, StorageException)

    """Raise an exception when argument is an empty string"""
    try:
        client.resumable.terminate("       ")
    except Exception as e:
        assert isinstance(e, StorageException)

    """Raise an exception when there's no fileinfo associated with the argument passed"""
    try:
        client.resumable.terminate("random_🐍.log")
    except Exception as e:
        assert isinstance(e, StorageException)


def test_sync_client(sync_client, file, test_bucket):
    client = sync_client

    """Check file was created during configuration phase"""
    assert file is not None

    """Verify test_bucket is not an empty string"""
    assert len(test_bucket.strip()) > 0

    client.resumable.create_unique_link(bucketname=test_bucket, filename=file.name)
    link = client.resumable.get_link(file.name)

    """Verify the link was generated as expected"""
    assert is_https_url(link)

    """Check the file is not empty"""
    assert os.stat(file.name).st_size > 0

    """Verify if the file was loaded correctly"""
    client.resumable.upload(file.name)
    bucket = client.from_(test_bucket)

    is_file_loaded = any(item["name"] == file.name for item in bucket.list())
    assert is_file_loaded, f"File not loaded:\n{bucket.list()}"

    try:
        client.resumable.terminate("")
    except Exception as e:
        assert isinstance(e, StorageException)

    bucket.remove(file.name)


def test_deferred_sync_client(sync_client, file, test_bucket):

    client = sync_client

    """Check file was created during configuration phase"""
    assert file is not None

    """Verify test_bucket is not an empty string"""
    assert len(test_bucket.strip()) > 0

    client.resumable.create_unique_link(bucketname=test_bucket, objectname=file.name)
    link = client.resumable.get_link(file.name)

    """Verify the link was generated as expected"""
    assert is_https_url(link)

    """Check the file is not empty"""
    assert os.stat(file.name).st_size > 0

    """Verify if the file was loaded correctly"""
    client.resumable.upload(
        file.name, mb_size=10, upload_defer=True, link=link, objectname=file.name
    )
    bucket = client.from_(test_bucket)

    is_file_loaded = any(item["name"] == file.name for item in bucket.list())
    assert is_file_loaded, f"File not loaded:\n{bucket.list()}"

    bucket.remove(file.name)


async def test_async_client(async_client, file, test_bucket):
    client = async_client

    """Check file was created during configuration phase"""
    assert file is not None

    """Verify test_bucket is not an empty string"""
    assert len(test_bucket.strip()) > 0

    await client.resumable.create_unique_link(
        bucketname=test_bucket, filename=file.name
    )
    link = client.resumable.get_link(file.name)

    """Verify the link was generated as expected"""
    assert is_https_url(link)

    """Check the file is not empty"""
    assert os.stat(file.name).st_size > 0

    """Verify if the file was loaded correctly"""
    await client.resumable.upload(file.name)
    bucket = client.from_(test_bucket)

    is_file_loaded = any(item["name"] == file.name for item in await bucket.list())
    assert is_file_loaded, f"File not loaded:\n{bucket.list()}"

    await bucket.remove(file.name)


async def test_deferred_async_client(async_client, file, test_bucket):

    client = async_client

    """Check file was created during configuration phase"""
    assert file is not None

    """Verify test_bucket is not an empty string"""
    assert len(test_bucket.strip()) > 0

    await client.resumable.create_unique_link(
        bucketname=test_bucket, objectname=file.name
    )
    link = client.resumable.get_link(file.name)

    """Verify the link was generated as expected"""
    assert is_https_url(link)

    """Check the file is not empty"""
    assert os.stat(file.name).st_size > 0

    """Verify if the file was loaded correctly"""
    await client.resumable.upload(
        file.name, mb_size=10, upload_defer=True, link=link, objectname=file.name
    )
    bucket = client.from_(test_bucket)

    is_file_loaded = any(item["name"] == file.name for item in await bucket.list())
    assert is_file_loaded, f"File not loaded:\n{bucket.list()}"

    await bucket.remove(file.name)
