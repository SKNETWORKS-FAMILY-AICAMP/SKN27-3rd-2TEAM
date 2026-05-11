from pydantic import BaseModel, ConfigDict, Field

from app.schemas.intent_state_schema import IntentType
from app.schemas.kag_input_schema import TargetSection


class RetrievalConstraintsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_evidence_per_track: int = Field(default=3, ge=1)
    require_content_id_match: bool = True


class RagInputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    user_id: str
    session_id: str
    intent_type: IntentType
    kag_recommended_content_ids: list[str] = Field(default_factory=list)
    target_section: TargetSection
    query_text: str
    evidence_need: list[str] = Field(default_factory=list)
    retrieval_constraints: RetrievalConstraintsSchema
