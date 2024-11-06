import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

import backoff
import requests

from .config import Config
from .exceptions import NeoApiError
from .models import LLMOutput

logger = logging.getLogger(__name__)


class NeoApiClientSync:
    """
    Synchronous Client for interacting with the Neo API to send LLM outputs.

    Manages batching of LLM outputs and sends them to the Neo API endpoints
    either periodically or when the batch size is reached.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        max_retries: int = 3,
        api_url: Optional[str] = None,
        check_frequency: int = 1,
    ):
        api_key = api_key or os.environ.get("NEOAPI_API_KEY")
        if not api_key:
            raise ValueError(
                "API key must be provided either directly or through NEOAPI_API_KEY environment variable."
            )
        if not api_key.strip():
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries

        self.api_url = (api_url or Config.API_URL).rstrip("/")
        self.check_frequency = check_frequency

        self.queue: List[LLMOutput] = []
        self._lock = threading.Lock()
        self._flush_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )
        self._semaphore = threading.Semaphore(100)
        self.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self) -> None:
        """
        Starts the NeoApiClientSync by initiating the background flush thread.
        """
        if self._flush_thread is None or not self._flush_thread.is_alive():
            logger.debug("Starting NeoApiClientSync.")
            self._stop_event.clear()
            self._flush_thread = threading.Thread(
                target=self._periodic_flush, daemon=True
            )
            self._flush_thread.start()
            logger.info("NeoApiClientSync started.")

    def stop(self) -> None:
        """
        Stops the NeoApiClientSync by signaling the flush thread to stop,
        flushing remaining items, and closing the HTTP session.
        """
        logger.debug("Stopping NeoApiClientSync.")
        self._stop_event.set()
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=self.flush_interval + 1)
            logger.debug("Flush thread terminated.")
        self.flush()  # Final flush of any remaining items
        self.session.close()
        logger.debug("Closed requests Session.")
        logger.info("NeoApiClientSync stopped.")

    def track(self, llm_output: LLMOutput) -> None:
        """
        Tracks an LLMOutput by adding it to the queue and sending the batch if
        the batch size is reached.

        Args:
            llm_output (LLMOutput): The LLMOutput item to track.
        """
        logger.debug(f"Tracking LLM output: {llm_output}")
        with self._lock:
            self.queue.append(llm_output)
            logger.debug(f"Queue size after append: {len(self.queue)}")
            if len(self.queue) >= self.batch_size:
                logger.debug("Batch size reached, preparing to flush.")
                batch = self.queue.copy()
                self.queue.clear()
                self._send_batch(batch)

    def flush(self) -> None:
        """
        Flushes the current queue by sending all queued LLMOutput items.
        """
        logger.debug("Attempting to flush the queue.")
        with self._lock:
            if not self.queue:
                logger.debug("Queue is empty, nothing to flush.")
                return
            batch = self.queue.copy()
            self.queue.clear()
            logger.debug(f"Flushing {len(batch)} items.")
        self._send_batch(batch)

    def _periodic_flush(self) -> None:
        """
        Periodically flushes the queue based on the flush interval.
        """
        logger.debug("Starting periodic flush thread.")
        while not self._stop_event.is_set():
            time.sleep(self.flush_interval)
            logger.debug("Periodic flush triggered.")
            self.flush()
        logger.debug("Exiting periodic flush thread.")

    def _send_batch(self, batch: List[LLMOutput]) -> None:
        """
        Sends a batch of LLMOutput items to the appropriate Neo API endpoints.

        Args:
            batch (List[LLMOutput]): The batch of LLMOutput items to send.
        """
        if not self.session:
            raise RuntimeError(
                "Client session is not initialized. Call start() before sending requests."
            )

        headers = self.session.headers

        logger.info(f"Sending batch of {len(batch)} LLM outputs to {self.api_url}.")

        threads = []
        for index, item in enumerate(batch):
            if index % self.check_frequency == 0:
                payload = item.model_dump()
                endpoint = "analyze" if item.need_analysis_response else "save"
                url = f"{self.api_url}/{endpoint}"

                logger.debug(
                    f"Preparing to send item to {url} with project: {payload.get('project')}, "
                    f"group: {payload.get('group')}, analysis_slug: {payload.get('analysis_slug')}."
                )

                thread = threading.Thread(
                    target=self._post_item, args=(url, payload, headers, item)
                )
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

    def _post_item(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        item: LLMOutput,
    ) -> None:
        if not self.session:
            raise RuntimeError("Client session is not initialized")

        session = self.session

        @backoff.on_exception(
            backoff.expo,
            (requests.RequestException, requests.Timeout),
            max_tries=self.max_retries,
            on_backoff=lambda details: logger.warning(
                f"Retrying send: Attempt {details['tries']} after {details['wait']} seconds."
            ),
        )
        def send_request() -> None:
            response = session.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code != 204 and not item.need_analysis_response:
                raise NeoApiError(f"Error {response.status_code}: {response.text}")
            elif item.need_analysis_response:
                try:
                    analysis_response = response.json()
                    if item.format_json_output:
                        formatted_response = json.dumps(analysis_response, indent=4)
                        logger.info(f"Analysis Response:\n{formatted_response}")
                    else:
                        logger.info(f"Analysis Response: {analysis_response}")
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON from analysis response.")
            else:
                logger.info("Successfully sent item.")

        try:
            send_request()
        except Exception as e:
            logger.exception(f"Failed to send item: {e}")

            with self._lock:
                self.queue.append(item)

    def batch_process(
        self,
        prompts: List[str],
        need_analysis_response: bool = False,
        format_json_output: bool = False,
        project: str = "default_project",
        group: str = "default_group",
        analysis_slug: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_text: bool = True,
    ) -> List[str]:
        from .decorators import track_llm_output

        logger.info(f"Starting batch processing of {len(prompts)} prompts")
        results = []

        @track_llm_output(
            client=self,
            project=project,
            group=group,
            analysis_slug=analysis_slug,
            need_analysis_response=need_analysis_response,
            format_json_output=format_json_output,
            metadata=metadata,
            save_text=save_text,
        )
        def process_single(prompt: str) -> str:
            logger.info(f"Processing prompt: {prompt}")
            result = prompt
            logger.info(f"Generated result: {result}")
            return result

        for i, prompt in enumerate(prompts, 1):
            logger.info(f"Processing item {i}/{len(prompts)}")
            result = process_single(prompt)
            results.append(result)
            logger.info(f"Completed item {i}")

        logger.info("Batch processing completed successfully")
        return results

    @classmethod
    def from_env(cls, **kwargs):
        api_key = os.getenv("NEOAPI_API_KEY")
        if not api_key:
            raise ValueError("NEOAPI_API_KEY environment variable is required")
        return cls(api_key=api_key, **kwargs)
