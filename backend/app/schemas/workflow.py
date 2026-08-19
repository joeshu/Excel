from typing import Literal

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    template_id: int
    name: str = Field(min_length=1, max_length=255)
    mode: Literal["formula", "manual", "dag", "template_native"] = "formula"


class DagUpdate(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)


class MappingUpdate(BaseModel):
    column_mapping: dict[str, str]


class NoticeWorkflowConfigUpdate(BaseModel):
    dimensions: dict = Field(default_factory=dict)
    rows: list[dict] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    totals: dict = Field(default_factory=dict)
    execution_mode: Literal["value", "formula"] = "value"


class MappingPreview(BaseModel):
    template_id: int
    data_source_id: int
    rules: list[dict] = Field(default_factory=list)


class MappingSnapshotCreate(BaseModel):
    data_source_id: int
    rules: list[dict] = Field(default_factory=list)


class MappingRuleCreate(BaseModel):
    data_source_id: int
    rules: list[dict] = Field(default_factory=list)


class TaskRunRequest(BaseModel):
    workflow_id: int
    data_source_id: int
    notice_config: dict[str, str] = Field(default_factory=dict)
    batch_id: str | None = None
    mapping_snapshot_id: int | None = None


class BatchTaskRunRequest(BaseModel):
    workflow_id: int
    data_source_ids: list[int] = Field(min_length=1)
    notice_config: dict[str, str] = Field(default_factory=dict)
    batch_id: str | None = None


class WorkflowMatchRequest(BaseModel):
    data_source_id: int


class WorkflowWizardCreate(BaseModel):
    template_id: int
    data_source_id: int
    name: str = Field(min_length=1, max_length=255)
    mode: Literal["formula", "dag", "template_native"] = "formula"
    column_mapping: dict[str, str] = Field(default_factory=dict)
    node_json: dict = Field(default_factory=dict)


class NoticeConfig(BaseModel):
    title: str = "Excel 通报表"
    period: str = ""
    publisher: str = ""
    as_of_date: str = ""
    signature: str = ""
    notes: str = ""
