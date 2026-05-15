from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.intent_state_schema import IntentType


TargetSection = Literal[
    "personalized_section",
    "discovery_section",
    "new_release_section",
]


class KagQueryContextSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalized_query: str = ""
    mood_candidates: list[str] = Field(default_factory=list)
    genre_candidates: list[str] = Field(default_factory=list)
    situation_candidates: list[str] = Field(default_factory=list)


class KagInputConstraintsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allow_discovery: bool = True
    allow_new_release: bool = True
    max_candidates: int = Field(default=10, ge=1)
    excluded_artists: list[str] = Field(default_factory=list)
    excluded_tracks: list[str] = Field(default_factory=list)
    excluded_genres: list[str] = Field(default_factory=list)


class KagInputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    user_id: str
    session_id: str
    intent_type: IntentType
    query_context: KagQueryContextSchema
    constraints: KagInputConstraintsSchema
