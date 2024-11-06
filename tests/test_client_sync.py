import threading
import time
from unittest.mock import Mock, patch

import pytest

from neoapi import LLMOutput, NeoApiClientSync


@pytest.fixture
def client():
    client = NeoApiClientSync(api_key="test_key", batch_size=2, flush_interval=0.1)
    with patch.object(client.session, "post") as mock_post:
        mock_post.return_value.status_code = 204
        yield client
        client.stop()


def test_track_and_flush(client):
    llm_output1 = LLMOutput(
        text="Test 1",
        timestamp=1234567890.0,
    )
    llm_output2 = LLMOutput(
        text="Test 2",
        timestamp=1234567891.0,
    )

    client.start()
    client.track(llm_output1)
    client.track(llm_output2)

    assert client.session.post.call_count >= 1
    assert len(client.queue) == 0


def test_client_initialization_error():
    with patch.dict("os.environ", clear=True):  # Clear environment variables
        with pytest.raises(ValueError):
            NeoApiClientSync(api_key=None)


def test_periodic_flush():
    with patch("requests.Session") as mock_session:
        mock_session.return_value.post.return_value.status_code = 204
        client = NeoApiClientSync(api_key="test_key", batch_size=5, flush_interval=0.1)

        client.start()
        llm_output = LLMOutput(
            text="Test",
            timestamp=1234567890.0,
        )
        client.track(llm_output)

        time.sleep(0.2)
        client.stop()

        assert mock_session.return_value.post.call_count >= 1


def test_concurrent_tracking(client):
    def track_items():
        for i in range(3):
            client.track(
                LLMOutput(
                    text=f"Test {i}",
                    timestamp=1234567890.0 + i,
                )
            )

    client.start()
    threads = [threading.Thread(target=track_items) for _ in range(3)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert client.session.post.call_count >= 1


def test_analysis_response(client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"analysis": "test"}
    client.session.post.return_value = mock_response

    llm_output = LLMOutput(
        text="Analyze this",
        timestamp=1234567890.0,
        need_analysis_response=True,
    )

    client.start()
    client.track(llm_output)
    client.flush()

    assert client.session.post.call_count >= 1
    last_call = client.session.post.call_args
    assert "/analyze" in last_call[0][0]


def test_batch_size_trigger(client):
    client.start()

    for i in range(client.batch_size + 1):
        client.track(LLMOutput(text=f"Test {i}", timestamp=1234567890.0 + i))

    assert client.session.post.call_count >= 1
    assert len(client.queue) <= client.batch_size


def test_stop_flushes_queue(client):
    client.start()

    for i in range(3):
        client.track(LLMOutput(text=f"Test {i}", timestamp=1234567890.0 + i))

    client.stop()
    assert len(client.queue) == 0
    assert client.session.post.call_count >= 1
