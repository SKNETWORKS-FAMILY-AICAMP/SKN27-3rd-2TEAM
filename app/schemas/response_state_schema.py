from pydantic import BaseModel, Field


class DisplayRecommendationSchema(BaseModel):
    content_id: str
    title: str
    artist: str
    label: str = ""
    display_reason: str


class ResponseStateSchema(BaseModel):
    status: str
    response_type: str
    chatbot_response: str
    display_recommendations: list[DisplayRecommendationSchema] = Field(default_factory=list)
    used_content_ids: list[str] = Field(default_factory=list)
