from unittest.mock import Mock

import pytest

from neoapi import NeoApiClientSync, track_llm_output


@pytest.fixture
def client():
    client = NeoApiClientSync(api_key="test_key")
    client.track = Mock()
    return client


def test_sync_decorator_basic(client):
    @track_llm_output(
        client=client,
        project="test_project",
        group="test_group",
        metadata={"test": "value"},
    )
    def test_function():
        return "test result"

    result = test_function()

    assert result == "test result"
    assert client.track.call_count == 1
    tracked_output = client.track.call_args[0][0]
    assert tracked_output.text == "test result"
    assert tracked_output.project == "test_project"
    assert tracked_output.group == "test_group"
    assert tracked_output.metadata == {"test": "value"}


def test_sync_decorator_with_exception(client):
    @track_llm_output(client=client)
    def failing_function():
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        failing_function()

    assert client.track.call_count == 0


def test_sync_decorator_with_analysis(client):
    @track_llm_output(
        client=client, need_analysis_response=True, format_json_output=True
    )
    def test_function():
        return "analyze this"

    result = test_function()

    assert result == "analyze this"
    tracked_output = client.track.call_args[0][0]
    assert tracked_output.need_analysis_response is True
    assert tracked_output.format_json_output is True


def test_sync_decorator_with_wrong_client():
    from neoapi import NeoApiClientAsync

    async_client = NeoApiClientAsync(api_key="test_key")

    @track_llm_output(client=async_client)
    def test_function():
        return "test result"

    result = test_function()
    assert result == "test result"


def test_sync_decorator_with_default_values(client):
    @track_llm_output(client=client)
    def test_function():
        return "default test"

    result = test_function()

    assert result == "default test"
    tracked_output = client.track.call_args[0][0]
    assert tracked_output.project == "default_project"
    assert tracked_output.group == "default_group"
    assert tracked_output.need_analysis_response is False
    assert tracked_output.format_json_output is False


def test_sync_decorator_with_none_values(client):
    @track_llm_output(client=client, metadata=None)
    def test_function():
        return "none values"

    result = test_function()

    assert result == "none values"
    tracked_output = client.track.call_args[0][0]
    assert tracked_output.project == "default_project"
    assert tracked_output.group == "default_group"
    assert tracked_output.metadata is None


def test_sync_decorator_return_types(client):
    @track_llm_output(client=client)
    def test_int():
        return 42

    @track_llm_output(client=client)
    def test_dict():
        return {"key": "value"}

    @track_llm_output(client=client)
    def test_list():
        return [1, 2, 3]

    assert test_int() == 42
    assert test_dict() == {"key": "value"}
    assert test_list() == [1, 2, 3]

    assert client.track.call_count == 3
    calls = client.track.call_args_list
    assert calls[0][0][0].text == "42"
    assert calls[1][0][0].text == "{'key': 'value'}"
    assert calls[2][0][0].text == "[1, 2, 3]"
