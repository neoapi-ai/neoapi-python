from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LLMOutput(BaseModel):
    model: str = "unknown"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    response: Any = None
    text: str
    timestamp: float
    project: str = "default_project"
    group: str = "default_group"
    analysis_slug: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    need_analysis_response: bool = False
    format_json_output: bool = False
    save_text: bool = True

    model_config = {"extra": "allow"}
