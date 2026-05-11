from pydantic import BaseModel, Field


class RecommendationGoalSchema(BaseModel):
    primary_goal: str


class KagStateSchema(BaseModel):
    status: str
    recommendation_goal: RecommendationGoalSchema
    recommended_content_ids: list[str] = Field(default_factory=list)
    recommendation_category: str
    route: str
    target_section: str
    traversal_reason: str = ""
    matched_nodes: list[dict] = Field(default_factory=list)
    excluded_nodes: list[dict] = Field(default_factory=list)
    candidate_tracks: list[dict] = Field(default_factory=list)
    diversity_metadata: dict = Field(default_factory=dict)
