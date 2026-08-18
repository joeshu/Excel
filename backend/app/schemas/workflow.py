from typing import Literal

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    template_id: int
    name: str = Field(min_length=1, max_length=255)
    mode: Literal["formula", "manual"] = "formula"


class MappingUpdate(BaseModel):
    column_mapping: dict[str, str]


class TaskRunRequest(BaseModel):
    workflow_id: int
    data_source_id: int
