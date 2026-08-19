import { Alert, Button, Card, Select, Space, Steps, Typography, Upload } from "antd";
import { UploadOutlined } from "@ant-design/icons";

type Source = { id: number; name: string };
type Workflow = { id: number; name: string; mode: string };
type NoticeConfig = { title: string };
type Preflight = { valid: boolean; missing_fields?: string[]; required_fields?: string[]; formula_risks?: { message: string; count: number }[] };

type GenerationWizardProps = {
  step: number;
  dataSourceId?: number;
  dataSources: Source[];
  workflows: Workflow[];
  workflowId?: number;
  workflowName?: string;
  noticeConfig: NoticeConfig;
  onUpload: (file: File) => Promise<boolean>;
  onSourceChange: (value: number) => void;
  onWorkflowChange: (value: number) => void;
  onMatch: () => void;
  onQuality: () => void;
  onNotice: () => void;
  onGenerate: () => void;
  canGenerate: boolean;
  preflight?: Preflight;
};

export function GenerationWizard(props: GenerationWizardProps) {
  const { step, dataSourceId, dataSources, workflows, workflowId, workflowName, onUpload, onSourceChange, onWorkflowChange, onMatch, onQuality, onNotice, onGenerate, canGenerate, preflight } = props;
  const stepContent = [
    { title: "导入数据", hint: "选择一份基础数据，系统会识别字段、类型和质量状态。" },
    { title: "选择工作流", hint: workflowName ? `当前工作流：${workflowName}` : "根据数据字段匹配适用的模板和工作流。" },
    { title: "质量预检", hint: "确认字段映射、公式依赖和数据质量后再继续。" },
    { title: "配置通报", hint: "补充标题、周期、发布单位和落款信息。" },
    { title: "生成成品", hint: "所有必需检查通过后提交生成任务。" },
  ][Math.min(step, 4)];
   return <Card className="wizard-shell" title={<div><Typography.Text className="card-kicker">日常生产</Typography.Text><Typography.Title level={3}>生成成品</Typography.Title></div>}><Steps current={step} items={[{ title: "上传基础明细" }, { title: "选择已配置工作流" }, { title: "结构与字段预检" }, { title: "通报配置" }, { title: "生成成品" }]} /><div className="wizard-step-content"><div className="wizard-step-intro"><Typography.Title level={4}>{stepContent.title}</Typography.Title><Typography.Text type="secondary">{stepContent.hint}</Typography.Text></div><div className="wizard-input-grid"><div><Typography.Text strong>1. 基础明细</Typography.Text><Space wrap className="wizard-inputs"><Upload beforeUpload={(file) => onUpload(file)} showUploadList={false}><Button icon={<UploadOutlined />}>上传基础明细</Button></Upload><Select value={dataSourceId} onChange={onSourceChange} placeholder="选择已有明细" options={dataSources.map((source) => ({ label: source.name, value: source.id }))} /></Space></div><div><Typography.Text strong>2. 已配置工作流</Typography.Text><Select className="wizard-workflow-select" value={workflowId} onChange={onWorkflowChange} placeholder="选择模板原生通报工作流" options={workflows.map((item) => ({ label: item.mode === "template_native" ? `${item.name} · 模板原生通报` : item.name, value: item.id }))} /></div></div>{preflight && <Alert type={preflight.valid ? "success" : "error"} showIcon message={preflight.valid ? "模板结构和字段预检通过" : `缺少字段：${preflight.missing_fields?.join("、") || "请完成模板配置"}`} description={preflight.formula_risks?.length ? `公式风险 ${preflight.formula_risks.length} 项，生成后需要在 Excel 中重算。` : undefined} /> }<div className="wizard-actions"><Button onClick={onMatch}>匹配工作流</Button><Button onClick={onQuality}>打开质量预检</Button><Button onClick={onNotice}>编辑通报配置</Button><Button type="primary" disabled={!canGenerate} onClick={onGenerate}>生成成品 Excel</Button></div></div><div className="wizard-footer"><Typography.Text type="secondary">模板配置只需完成一次，后续每次上传新的基础明细即可。</Typography.Text><Typography.Text type="secondary">{workflowName ? `当前：${workflowName}` : "等待选择已配置工作流"}</Typography.Text></div></Card>;
}
