import { Button } from "antd";
import { EmptyState } from "./EmptyState";
import { MappingCenter } from "./MappingCenter";
import { PageHeader } from "./PageHeader";

type Column = { mappingKey: string; sheet: string; column: string; header?: string; type: string };
type Field = { field: string; type: string; quality_status?: string; quality_messages?: string[]; non_empty_rate?: number };

export function MappingPage({ workflowName, columns, fields, mapping, fieldOptions, qualityFilter, onBack, onSave, onPreview, onSaveSnapshot, onMappingChange, onQualityFilterChange }: {
  workflowName?: string;
  columns: Column[];
  fields: Field[];
  mapping: Record<string, string>;
  fieldOptions: { label: string; value: string }[];
  qualityFilter: string;
  onBack: () => void;
  onSave: () => void;
  onPreview: () => void;
  onSaveSnapshot: () => void;
  onMappingChange: (key: string, value: string) => void;
  onQualityFilterChange: (value: string) => void;
}) {
  if (!workflowName) return <EmptyState title="请先选择或创建工作流" description="从模板中心打开模式 A 工作流后，再进行字段映射和预检。" action={<Button onClick={onBack}>前往模板中心</Button>} />;
  return <><PageHeader eyebrow="WORKFLOW CENTER" title="模板与基础数据映射" description={`当前工作流：${workflowName}`} actions={<><Button onClick={onBack}>返回模板中心</Button><Button onClick={onSave}>保存映射</Button><Button onClick={onPreview}>映射预检</Button><Button type="primary" onClick={onSaveSnapshot}>保存映射快照</Button></>} /><MappingCenter columns={columns} fields={fields} mapping={mapping} fieldOptions={fieldOptions} onMappingChange={onMappingChange} qualityFilter={qualityFilter} onQualityFilterChange={onQualityFilterChange} /></>;
}
