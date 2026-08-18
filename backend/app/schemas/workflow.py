from typing import Literal

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    template_id: int
    name: str = Field(min_length=1, max_length=255)
    mode: Literal["formula", "manual", "dag"] = "formula"


class DagUpdate(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)


class MappingUpdate(BaseModel):
    column_mapping: dict[str, str]


class TaskRunRequest(BaseModel):
    workflow_id: int
    data_source_id: int
    notice_config: dict[str, str] = Field(default_factory=dict)
    batch_id: str | None = None


class BatchTaskRunRequest(BaseModel):
    workflow_id: int
    data_source_ids: list[int] = Field(min_length=1)
    notice_config: dict[str, str] = Field(default_factory=dict)
    batch_id: str | None = None
