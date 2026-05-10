from pydantic import BaseModel, ConfigDict, Field


class MusicDetailViewModelSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_id: str
    title: str
    artist: str
    display_reason: str = ""
    evidence_summary: str = ""
    album: str | None = None
    genre: list[str] = Field(default_factory=list)
    mood: list[str] = Field(default_factory=list)
    source: str
