from typing import List, Optional
from pydantic import BaseModel, Field


class AiConfigUpdate(BaseModel):
    api_key: Optional[str] = Field(None)
    ai_model: Optional[str] = Field(None, max_length=100)
    ai_base_url: Optional[str] = Field(None, max_length=255)


class AiChatMessage(BaseModel):
    role: str
    content: str


class AiChatRequest(BaseModel):
    messages: List[AiChatMessage]
    context: Optional[str] = None
