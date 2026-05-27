from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BudgetBand = Literal["low", "medium", "high"]

# config/ -> backend/ -> Phase 5/ -> docs/ -> Zomato/ (repo root)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_DIR = PROJECT_ROOT / ".cache"
CANONICAL_ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(CANONICAL_ENV_FILE),  # absolute path → single source of truth
        env_file_encoding="utf-8",
        extra="ignore",
    )

    hf_dataset_id: str = Field(
        default="ManikaSaini/zomato-restaurant-recommendation",
        alias="HF_DATASET_ID",
    )
    hf_home: Path = Field(
        default=DEFAULT_CACHE_DIR / "huggingface",
        alias="HF_HOME",
    )
    restaurant_cache_path: Path = Field(
        default=DEFAULT_CACHE_DIR / "restaurants.parquet",
        alias="RESTAURANT_CACHE_PATH",
    )

    budget_low_max: int = Field(default=500, alias="BUDGET_LOW_MAX")
    budget_medium_max: int = Field(default=1500, alias="BUDGET_MEDIUM_MAX")

    hf_download_retries: int = Field(default=3, alias="HF_DOWNLOAD_RETRIES")
    hf_download_backoff_seconds: float = Field(
        default=2.0,
        alias="HF_DOWNLOAD_BACKOFF_SECONDS",
    )

    default_min_rating: float = Field(default=3.0, alias="DEFAULT_MIN_RATING")
    default_budget: BudgetBand = Field(default="medium", alias="DEFAULT_BUDGET")
    additional_max_length: int = Field(default=500, alias="ADDITIONAL_MAX_LENGTH")

    candidate_cap: int = Field(default=30, alias="CANDIDATE_CAP")
    candidate_cap_max: int = Field(default=50, alias="CANDIDATE_CAP_MAX")
    recommendation_top_k: int = Field(default=5, alias="RECOMMENDATION_TOP_K")
    prompt_field_max_length: int = Field(default=120, alias="PROMPT_FIELD_MAX_LENGTH")
    log_prompts: bool = Field(default=False, alias="LOG_PROMPTS")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        alias="GROQ_MODEL",
    )
    groq_temperature: float = Field(default=0.2, alias="GROQ_TEMPERATURE")
    groq_max_tokens: int = Field(default=2048, alias="GROQ_MAX_TOKENS")
    llm_timeout_seconds: float = Field(default=60.0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    llm_retry_backoff_seconds: float = Field(
        default=2.0,
        alias="LLM_RETRY_BACKOFF_SECONDS",
    )
    log_llm_responses: bool = Field(default=False, alias="LOG_LLM_RESPONSES")

    # Phase 6: rate limiting (recommendations endpoint only)
    rate_limit_per_minute: int = Field(
        default=30,
        alias="RATE_LIMIT_PER_MINUTE",
        description="Max POST /recommendations calls per IP per minute (SlowAPI)",
    )

    @field_validator("hf_home", "restaurant_cache_path", mode="before")
    @classmethod
    def _expand_path(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()

    @model_validator(mode="after")
    def _validate_budget_thresholds(self) -> "Settings":
        if self.budget_low_max <= 0:
            raise ValueError("BUDGET_LOW_MAX must be positive")
        if self.budget_medium_max <= self.budget_low_max:
            raise ValueError(
                "BUDGET_MEDIUM_MAX must be greater than BUDGET_LOW_MAX"
            )
        if self.candidate_cap <= 0:
            raise ValueError("CANDIDATE_CAP must be positive")
        if self.candidate_cap_max < self.candidate_cap:
            raise ValueError("CANDIDATE_CAP_MAX must be >= CANDIDATE_CAP")
        if self.recommendation_top_k <= 0:
            raise ValueError("RECOMMENDATION_TOP_K must be positive")
        if self.llm_max_retries <= 0:
            raise ValueError("LLM_MAX_RETRIES must be positive")
        if self.groq_max_tokens <= 0:
            raise ValueError("GROQ_MAX_TOKENS must be positive")
        return self

    def cost_to_budget_band(self, cost_inr: int | None) -> BudgetBand | None:
        if cost_inr is None:
            return None
        if cost_inr <= self.budget_low_max:
            return "low"
        if cost_inr <= self.budget_medium_max:
            return "medium"
        return "high"


@lru_cache
def get_settings() -> Settings:
    return Settings()
