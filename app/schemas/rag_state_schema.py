from typing import Literal

from pydantic import BaseModel, Field


class RagEvidenceSchema(BaseModel):
    content_id: str
    title: str
    artist: str
    genre: list[str] = Field(default_factory=list)
    mood: list[str] = Field(default_factory=list)
    evidence_summary: str


class RecommendationReasonSchema(BaseModel):
    summary: str


class RagStateSchema(BaseModel):
    status: Literal["success", "failed", "fallback"]
    query: str = ""
    normalized_query: str = ""
    recommended_content_evidence: list[RagEvidenceSchema] = Field(default_factory=list)
    recommendation_reason: RecommendationReasonSchema
    retrieval_metadata: dict = Field(default_factory=dict)
    retrieval_trace: dict = Field(default_factory=dict)
