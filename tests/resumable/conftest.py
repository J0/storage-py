from __future__ import annotations

import asyncio
import os
from urllib.parse import urlparse

import pytest
import pytest_asyncio

from storage3 import AsyncStorageClient, SyncStorageClient


def is_https_url(url: str) -> bool:
    """Simple helper that checks if string argument is an HTTPS URL."""
    return urlparse(url).scheme == "https"


@pytest.fixture
def file() -> str:
    """Simple helper that writes an SVG file."""
    file_name = "test_image.svg"
    # Supabase logo SVG, for testing purposes only.
    file_content = b"""
        <svg width="109" height="113" viewBox="0 0 109 113" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935
        40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint0_linear)"/>
        <path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935
        40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint1_linear)"
        fill-opacity="0.2"/> <path d="M45.317 2.07103C48.1765 -1.53037 53.9745 0.442937 54.0434 5.041L54.4849
        72.2922H9.83113C1.64038 72.2922 -2.92775 62.8321 2.1655 56.4175L45.317 2.07103Z" fill="#3ECF8E"/> <defs>
        <linearGradient id="paint0_linear" x1="53.9738" y1="54.974" x2="94.1635" y2="71.8295"
        gradientUnits="userSpaceOnUse"> <stop stop-color="#249361"/> <stop offset="1" stop-color="#3ECF8E"/>
        </linearGradient> <linearGradient id="paint1_linear" x1="36.1558" y1="30.578" x2="54.4844" y2="65.0806"
        gradientUnits="userSpaceOnUse"> <stop/> <stop offset="1" stop-opacity="0"/> </linearGradient> </defs> </svg>
    """.strip()

    with open(file_name, "wb") as f:
        f.write(file_content)

    return f


@pytest_asyncio.fixture(scope="package")
def event_loop() -> asyncio.AbstractEventLoop:
    """Returns an event loop for the current thread"""
    return asyncio.get_event_loop_policy().get_event_loop()


@pytest.fixture
def test_bucket() -> str:
    """Get Bucket name from env args."""
    return os.getenv("TEST_BUCKET")


@pytest.fixture(scope="module")
def configure_client():
    """Get API URL and API Key from env args."""
    url = f'{os.getenv("SUPABASE_URL")}/storage/v1'
    key = os.getenv("SUPABASE_KEY")
    return (url, key)


@pytest.fixture(scope="module")
def sync_client(configure_client) -> SyncStorageClient:
    """Simple helper that returns an SyncStorageClient."""
    url, key = configure_client
    client = SyncStorageClient(url, {"apiKey": key, "Authorization": f"Bearer {key}"})
    return client


@pytest.fixture(scope="module")
def async_client(configure_client) -> AsyncStorageClient:
    """Simple helper that returns an AsyncStorageClient."""
    url, key = configure_client
    client = AsyncStorageClient(url, {"apiKey": key, "Authorization": f"Bearer {key}"})
    return client
