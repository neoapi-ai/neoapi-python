import asyncio
from unittest.mock import AsyncMock

import pytest

from neoapi import LLMOutput, NeoApiClientAsync


@pytest.fixture
def client():
    return NeoApiClientAsync(
        api_key="test_key",
        initial_batch_size=2,
        initial_flush_interval=0.1,
        adjustment_interval=1.0,
    )


@pytest.mark.asyncio
async def test_track_and_flush(client):
    client._send_batch = AsyncMock()
    await client.start()

    llm_output1 = LLMOutput(text="Test 1", timestamp=1234567890.0)
    llm_output2 = LLMOutput(text="Test 2", timestamp=1234567891.0)

    await client.track(llm_output1)
    await client.track(llm_output2)

    await asyncio.sleep(0.1)
    client._send_batch.assert_awaited_once_with([llm_output1, llm_output2])

    await client.stop()


@pytest.mark.asyncio
async def test_client_initialization_error(monkeypatch):
    monkeypatch.delenv("NEOAPI_API_KEY", raising=False)
    with pytest.raises(
        ValueError,
        match="API key must be provided either directly or through NEOAPI_API_KEY environment variable",
    ):
        NeoApiClientAsync(api_key=None)


@pytest.mark.asyncio
async def test_send_without_start():
    client = NeoApiClientAsync(api_key="test_key")
    llm_output = LLMOutput(text="Test", timestamp=1234567890.0)

    with pytest.raises(RuntimeError, match="Client session is not initialized"):
        await client._send_batch([llm_output])


@pytest.mark.asyncio
async def test_concurrent_tracking(client):
    await client.start()
    client._send_batch = AsyncMock()

    outputs = [
        LLMOutput(text=f"Test {i}", timestamp=1234567890.0 + i) for i in range(5)
    ]

    await asyncio.gather(*(client.track(output) for output in outputs))

    await asyncio.sleep(0.1)

    assert client._send_batch.call_count == 3

    await client.stop()


@pytest.mark.asyncio
async def test_periodic_flush():
    client = NeoApiClientAsync(
        api_key="test_key",
        initial_batch_size=10,
        initial_flush_interval=0.1,
        adjustment_interval=1.0,
    )
    client._send_batch = AsyncMock()
    await client.start()

    llm_output = LLMOutput(text="Test", timestamp=1234567890.0)
    await client.track(llm_output)

    await asyncio.sleep(0.2)
    client._send_batch.assert_called_once_with([llm_output])

    await client.stop()


@pytest.mark.asyncio
async def test_client_initialization_from_env(monkeypatch):
    monkeypatch.setenv("NEOAPI_API_KEY", "test_env_key")
    client = NeoApiClientAsync()
    assert client.api_key == "test_env_key"
