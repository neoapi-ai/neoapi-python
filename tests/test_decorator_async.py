from unittest.mock import AsyncMock, Mock

import pytest

from neoapi import NeoApiClientAsync, NeoApiClientSync, track_llm_output


@pytest.fixture(scope="function")
def client():
    client = NeoApiClientAsync(api_key="test_key")
    client.track = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_async_decorator(client):
    @track_llm_output(
        client=client,
        project="test_project",
        group="test_group",
        metadata={"test": "value"},
    )
    async def test_function():
        return "test result"

    result = await test_function()

    assert result == "test result"
    assert client.track.call_count == 1
    tracked_output = client.track.call_args[0][0]
    assert tracked_output.text == "test result"
    assert tracked_output.project == "test_project"
    assert tracked_output.group == "test_group"
    assert tracked_output.metadata == {"test": "value"}


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_sync_decorator():
    client = NeoApiClientSync(api_key="test_key")
    client.track = Mock()

    @track_llm_output(client=client)
    def test_function():
        return "sync result"

    result = test_function()

    assert result == "sync result"
    assert client.track.call_count == 1
    tracked_output = client.track.call_args[0][0]
    assert tracked_output.text == "sync result"


@pytest.mark.asyncio
async def test_decorator_with_exception(client):
    @track_llm_output(client=client)
    async def failing_function():
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        await failing_function()

    assert client.track.call_count == 0


@pytest.mark.asyncio
async def test_decorator_with_analysis_response(client):
    @track_llm_output(
        client=client, need_analysis_response=True, format_json_output=True
    )
    async def test_function():
        return "analyze this"

    result = await test_function()

    assert result == "analyze this"
    tracked_output = client.track.call_args[0][0]
    assert tracked_output.need_analysis_response is True
    assert tracked_output.format_json_output is True
