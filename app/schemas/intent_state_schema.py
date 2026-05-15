from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


IntentType = Literal[
    "personalized_recommendation",
    "new_release_recommendation",
    "discovery_recommendation",
    "music_information",
    "recommendation_reason",
    "general_chat",
]


class IntentStateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    normalized_query: str = ""
    detected_moods: list[str] = Field(default_factory=list)
    detected_genres: list[str] = Field(default_factory=list)
    detected_artists: list[str] = Field(default_factory=list)
    detected_situations: list[str] = Field(default_factory=list)
    requested_count: int | None = Field(default=None, ge=1)
    disliked_artists: list[str] = Field(default_factory=list)
    disliked_tracks: list[str] = Field(default_factory=list)
    disliked_genres: list[str] = Field(default_factory=list)
    requires_kag: bool
    requires_rag: bool
