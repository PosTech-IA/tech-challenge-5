from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AnalysisStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    ERROR = "error"


class AnalysisSchema(BaseModel):
    id: str
    filename: str
    file_ref: str
    status: AnalysisStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcessQueueMessage(BaseModel):
    analysis_id: str
    file_ref: str


class ResultQueueMessage(BaseModel):
    analysis_id: str
    components: list[str] = Field(min_length=1)
    risks: list[str] = Field(min_length=1)
    recommendations: list[str] = Field(min_length=1)


class ReportSchema(BaseModel):
    id: str
    analysis_id: str
    components: list[str]
    risks: list[str]
    recommendations: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
