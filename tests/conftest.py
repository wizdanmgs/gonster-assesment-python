import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from main import create_app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
