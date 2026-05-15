from pydantic import BaseModel, Field


class SessionContextSchema(BaseModel):
    session_id: str
    recent_genres: list[str] = Field(default_factory=list)
    recent_artists: list[str] = Field(default_factory=list)
    recent_moods: list[str] = Field(default_factory=list)
    selected_tracks: list[str] = Field(default_factory=list)
    disliked_artists: list[str] = Field(default_factory=list)
    disliked_tracks: list[str] = Field(default_factory=list)
    disliked_genres: list[str] = Field(default_factory=list)
    conversation_summary: str = ""
