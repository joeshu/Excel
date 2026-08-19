import { ArrowRightOutlined, BranchesOutlined, CalculatorOutlined, FormOutlined, LayoutOutlined } from "@ant-design/icons";
import { Button, Card, Empty, Space, Tag, Typography } from "antd";

type Workflow = { id: number; name: string; mode: string; template_id: number };
type Template = { id: number; name: string; version: string };

type Props = {
  workflows: Workflow[];
  templates: Template[];
  onOpen: (mode: string) => void;
  onWorkflow: (workflow: Workflow) => void;
};

const modes = [
  { key: "template_native", title: "模板原生通报", eyebrow: "REPORT WORKSPACE", description: "保留通报页、明细页、样式和公式口径，适合正式通报生产。", icon: <LayoutOutlined />, accent: "native", steps: ["分析模板结构", "确认组织与指标映射", "预览并生成成品"] },
  { key: "formula", title: "模式 A · 公式模板", eyebrow: "FORMULA MAPPING", description: "按列绑定基础字段，保留模板公式，适合结构稳定的简单模板。", icon: <CalculatorOutlined />, accent: "formula", steps: ["选择模板列", "绑定基础字段", "填充数据并重算"] },
  { key: "dag", title: "模式 B · 流程编排", eyebrow: "VISUAL PIPELINE", description: "用节点编排字段计算、条件筛选和模板输出，适合多步骤数据处理。", icon: <BranchesOutlined />, accent: "dag", steps: ["添加数据源节点", "配置计算与条件", "连接节点并运行"] },
  { key: "manual", title: "手工配置", eyebrow: "MANUAL CONTROL", description: "逐列确认字段、常量或保留模板值，适合特殊格式和人工复核场景。", icon: <FormOutlined />, accent: "manual", steps: ["选择输出列", "配置来源策略", "确认后导出"] },
];

export function WorkflowModeCenter({ workflows, templates, onOpen, onWorkflow }: Props) {
  return <div className="mode-center-page"><div className="mode-center-hero"><Typography.Text className="eyebrow">WORKFLOW MODE CENTER</Typography.Text><Typography.Title level={2}>选择一条清晰的生产路径</Typography.Title><Typography.Paragraph>每种模式拥有独立配置入口、校验规则和执行方式，覆盖复杂通报、公式模板、流程编排和手工复核。</Typography.Paragraph></div><div className="mode-card-grid">{modes.map((mode) => { const items = workflows.filter((item) => item.mode === mode.key); return <Card key={mode.key} className={`mode-card mode-card-${mode.accent}`}><div className="mode-card-head"><div className="mode-icon">{mode.icon}</div><div><Typography.Text className="card-kicker">{mode.eyebrow}</Typography.Text><Typography.Title level={3}>{mode.title}</Typography.Title></div></div><Typography.Paragraph type="secondary">{mode.description}</Typography.Paragraph><div className="mode-step-list">{mode.steps.map((step, index) => <div key={step}><span>{String(index + 1).padStart(2, "0")}</span>{step}</div>)}</div><Space wrap><Button type={mode.key === "template_native" ? "primary" : "default"} onClick={() => onOpen(mode.key)}>进入{mode.title}</Button><Tag>{items.length} 个工作流</Tag></Space>{items.length > 0 && <div className="mode-recent"><Typography.Text type="secondary">最近配置</Typography.Text>{items.slice(0, 2).map((item) => <Button key={item.id} type="link" onClick={() => onWorkflow(item)}>{item.name} <ArrowRightOutlined /></Button>)}</div>}</Card>; })}</div><Card className="mode-selection-note"><Space align="start"><Tag color="cyan">建议</Tag><div><Typography.Text strong>复杂模板优先使用“模板原生通报”</Typography.Text><Typography.Paragraph type="secondary">它支持从带公式副本提取口径，并允许后续编辑组织映射、指标公式、排名区间和历史版本。</Typography.Paragraph></div></Space>{templates.length === 0 && <Empty description="请先上传模板" />}</Card></div>;
}
