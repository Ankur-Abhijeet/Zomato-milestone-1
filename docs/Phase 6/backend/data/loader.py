"""Download the Hugging Face Zomato dataset."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Iterable

from datasets import load_dataset

from config.settings import Settings
from data.preprocessor import validate_raw_schema

logger = logging.getLogger(__name__)


class DatasetLoadError(RuntimeError):
    """Raised when the Hugging Face dataset cannot be loaded."""


def _configure_hf_env(settings: Settings) -> None:
    settings.hf_home.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(settings.hf_home))


def download_raw_rows(settings: Settings) -> Iterable[dict[str, Any]]:
    _configure_hf_env(settings)
    last_error: Exception | None = None

    for attempt in range(1, settings.hf_download_retries + 1):
        try:
            logger.info(
                "Downloading dataset %s (attempt %d/%d)",
                settings.hf_dataset_id,
                attempt,
                settings.hf_download_retries,
            )
            dataset = load_dataset(settings.hf_dataset_id, split="train")
            validate_raw_schema(dataset.column_names)
            logger.info("Downloaded %d raw rows", len(dataset))
            # Return a generator to save ~50MB of RAM during startup
            return (dict(row) for row in dataset)
        except Exception as exc:
            last_error = exc
            logger.warning("Dataset download failed: %s", exc)
            if attempt < settings.hf_download_retries:
                sleep_for = settings.hf_download_backoff_seconds * attempt
                time.sleep(sleep_for)

    raise DatasetLoadError(
        f"Could not download dataset '{settings.hf_dataset_id}' after "
        f"{settings.hf_download_retries} attempts. "
        f"Check network connectivity or set RESTAURANT_CACHE_PATH to an "
        f"existing offline cache. Last error: {last_error}"
    ) from last_error
