from pydantic import BaseModel, Field


class IngestionResponse(BaseModel):
    filename: str
    namespace: str
    chunks: int
    vector_ids: list[str] = Field(default_factory=list)
    message: str = "Document ingested successfully"


class TextIngestionRequest(BaseModel):
    text: str = Field(..., min_length=10)
    namespace: str
    source_label: str = "manual-input"


class NamespaceStatsResponse(BaseModel):
    namespace: str
    has_content: bool
