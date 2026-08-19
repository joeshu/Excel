import { Button, Card, Select, Space, Tag, Typography } from "antd";

type Template = { id: number; name: string; version: string; has_formula?: boolean };

type Props = { mode: string; templates: Template[]; onBack: () => void; onSelect: (template: Template) => void };

const copy: Record<string, { title: string; description: string; action: string }> = {
  template_native: { title: "配置模板原生通报", description: "先选择模板，系统会分析通报页、明细页、组织行和公式口径。", action: "分析并配置模板" },
  formula: { title: "配置模式 A 公式模板", description: "先选择模板，再进入输出列与基础字段映射。", action: "进入列映射" },
  dag: { title: "配置模式 B 流程编排", description: "先选择模板，再进入数据源、公式、条件和输出节点设计。", action: "进入流程设计" },
  manual: { title: "配置手工工作流", description: "先选择模板，再逐列确认字段、常量或保留模板值。", action: "进入手工配置" },
};

export function WorkflowModeSetup({ mode, templates, onBack, onSelect }: Props) {
  const item = copy[mode] ?? copy.manual;
  return <div className="mode-setup-page"><Card className={`mode-setup-card mode-setup-${mode}`}><Typography.Text className="card-kicker">独立配置入口</Typography.Text><Typography.Title level={2}>{item.title}</Typography.Title><Typography.Paragraph type="secondary">{item.description}</Typography.Paragraph><Space direction="vertical" size="large" className="wide"><Typography.Text strong>选择模板</Typography.Text><Select size="large" placeholder="选择模板版本" className="wide" options={templates.map((template) => ({ label: `${template.name} · v${template.version}${template.has_formula ? " · 含公式" : ""}`, value: template.id, template }))} onChange={(_value, option) => onSelect((option as { template: Template }).template)} /><Space wrap><Button onClick={onBack}>返回模式中心</Button><Tag>{templates.length} 个模板可用</Tag></Space></Space></Card></div>;
}
